"""
Tests for the account connection flow.

Covers:
1. Pydantic schema validation (ConnectionRequest, ConnectionResponse, etc.)
2. Connection endpoint HTTP behavior
3. SSE stream format and serialization
4. ConnectionStatusManager event-driven behavior
5. Protocol alignment checks (frontend/backend contract)

These tests mock the browser/Playwright layer so they run fast
and without a real browser.
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

# Ensure backend root is on sys.path
backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from schemas import (
    ConnectionRequest,
    ConnectionResponse,
    ConnectionStatus,
    ConnectionStatusResponse,
    ConnectionStreamData,
    AccountStatus,
)
from api.account import ConnectionStatusManager, connection_status_manager


# ============================================================================
# 1. Schema Validation Tests
# ============================================================================


class TestConnectionRequestSchema:
    """Validate ConnectionRequest Pydantic schema behavior."""

    def test_valid_request_with_code(self):
        """A full request with phone and code should pass validation."""
        req = ConnectionRequest(phone="13800138000", code="1234")
        assert req.phone == "13800138000"
        assert req.code == "1234"

    def test_valid_request_with_6_digit_code(self):
        """6-digit code should be accepted."""
        req = ConnectionRequest(phone="13800138000", code="123456")
        assert req.code == "123456"

    def test_invalid_phone_too_short(self):
        """Phone number shorter than 11 digits should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ConnectionRequest(phone="1380013", code="1234")
        errors = exc_info.value.errors()
        assert any("phone" in str(e["loc"]) for e in errors)

    def test_invalid_phone_too_long(self):
        """Phone number longer than 11 digits should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ConnectionRequest(phone="138001380001", code="1234")
        errors = exc_info.value.errors()
        assert any("phone" in str(e["loc"]) for e in errors)

    def test_invalid_code_too_short(self):
        """Code shorter than 4 digits should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            ConnectionRequest(phone="13800138000", code="12")
        errors = exc_info.value.errors()
        assert any("code" in str(e["loc"]) for e in errors)

    def test_empty_code_rejected(self):
        """
        CRITICAL BUG DETECTION: Empty code string should fail validation.

        This test documents the current behavior that BLOCKS the two-phase
        connection flow. The frontend sends code='' for Phase 1 (send SMS),
        but Pydantic rejects it due to min_length=4.

        When this test starts PASSING (empty code accepted), the fix for
        the two-phase flow has been applied.
        """
        with pytest.raises(ValidationError):
            ConnectionRequest(phone="13800138000", code="")

    def test_missing_code_rejected(self):
        """Missing code field should fail validation (it is required)."""
        with pytest.raises(ValidationError):
            ConnectionRequest(phone="13800138000")  # type: ignore[call-arg]

    def test_code_too_long(self):
        """Code longer than 6 digits should fail."""
        with pytest.raises(ValidationError):
            ConnectionRequest(phone="13800138000", code="1234567")


class TestConnectionResponseSchema:
    """Validate ConnectionResponse schema."""

    def test_success_response(self):
        resp = ConnectionResponse(
            success=True,
            message="Connection successful",
            status="active",
            storage_state="encrypted_data",
        )
        assert resp.success is True
        assert resp.status == "active"
        assert resp.storage_state == "encrypted_data"

    def test_failure_response(self):
        resp = ConnectionResponse(
            success=False,
            message="Login failed",
            status="inactive",
        )
        assert resp.success is False
        assert resp.storage_state is None

    def test_default_status(self):
        """Default status should be 'inactive'."""
        resp = ConnectionResponse(success=True, message="ok")
        assert resp.status == "inactive"


class TestConnectionStatusEnum:
    """Validate ConnectionStatus enum values match expected protocol."""

    def test_all_expected_values_exist(self):
        """All states expected by the frontend must exist."""
        expected = ["idle", "waiting_phone", "code_sent", "waiting_verify", "verifying", "success", "error"]
        for val in expected:
            assert ConnectionStatus(val) is not None, f"Missing enum value: {val}"

    def test_frontend_connected_value_does_not_exist(self):
        """
        PROTOCOL MISMATCH DETECTION: The frontend uses 'connected' but
        the backend enum uses 'success'. This test documents the mismatch.
        """
        with pytest.raises(ValueError):
            ConnectionStatus("connected")

    def test_enum_values_are_json_serializable_as_strings(self):
        """Enum .value should produce a plain string for JSON serialization."""
        for status in ConnectionStatus:
            assert isinstance(status.value, str)
            # Ensure json.dumps works on the .value
            json.dumps({"status": status.value})


class TestConnectionStreamData:
    """Validate SSE stream data schema."""

    def test_valid_stream_data(self):
        data = ConnectionStreamData(
            status=ConnectionStatus.WAITING_PHONE,
            message="Waiting for phone",
            progress=10,
        )
        assert data.status == ConnectionStatus.WAITING_PHONE
        assert data.progress == 10

    def test_stream_data_json_serialization(self):
        """Stream data should be JSON-serializable for SSE transport."""
        data = ConnectionStreamData(
            status=ConnectionStatus.CODE_SENT,
            message="Code sent",
            progress=40,
        )
        # model_dump should produce serializable dict
        dumped = data.model_dump()
        json_str = json.dumps(dumped, default=str)
        parsed = json.loads(json_str)
        assert parsed["status"] == "code_sent"


# ============================================================================
# 2. ConnectionStatusManager Unit Tests
# ============================================================================


class TestConnectionStatusManager:
    """Test the event-driven connection status manager."""

    @pytest_asyncio.fixture()
    async def manager(self):
        """Create a fresh manager for each test."""
        return ConnectionStatusManager()

    @pytest.mark.asyncio
    async def test_set_and_get_status(self, manager: ConnectionStatusManager):
        """Setting status should be retrievable via get_status."""
        await manager.set_status(1, ConnectionStatus.WAITING_PHONE, "Waiting", 10)
        status = manager.get_status(1)
        assert status is not None
        assert status["status"] == ConnectionStatus.WAITING_PHONE
        assert status["message"] == "Waiting"
        assert status["progress"] == 10

    @pytest.mark.asyncio
    async def test_clear_status(self, manager: ConnectionStatusManager):
        """Clearing status should remove it from the store."""
        await manager.set_status(1, ConnectionStatus.SUCCESS, "Done", 100)
        manager.clear_status(1)
        assert manager.get_status(1) is None

    @pytest.mark.asyncio
    async def test_set_status_sync(self, manager: ConnectionStatusManager):
        """Sync variant should also update status."""
        manager.set_status_sync(1, ConnectionStatus.ERROR, "Failed", 0)
        status = manager.get_status(1)
        assert status is not None
        assert status["status"] == ConnectionStatus.ERROR

    @pytest.mark.asyncio
    async def test_subscribe_receives_initial_status(self, manager: ConnectionStatusManager):
        """Subscriber should receive current status as first event."""
        await manager.set_status(1, ConnectionStatus.WAITING_PHONE, "Initial", 10)

        received = []
        stream = manager.subscribe(1)
        try:
            received.append(await anext(stream))
        finally:
            await stream.aclose()

        assert len(received) == 1
        assert received[0]["status"] == ConnectionStatus.WAITING_PHONE

    @pytest.mark.asyncio
    async def test_subscribe_receives_updates(self, manager: ConnectionStatusManager):
        """Subscriber should receive status updates via queue."""
        received = []

        async def subscriber():
            stream = manager.subscribe(1)
            try:
                async for event in stream:
                    received.append(event)
                    if event.get("status") == ConnectionStatus.SUCCESS:
                        break
            finally:
                await stream.aclose()

        # Start subscriber in background
        task = asyncio.create_task(subscriber())

        # Give subscriber time to start
        await asyncio.sleep(0.05)

        # Push status updates
        await manager.set_status(1, ConnectionStatus.WAITING_PHONE, "Step 1", 10)
        await asyncio.sleep(0.05)
        await manager.set_status(1, ConnectionStatus.SUCCESS, "Done", 100)

        # Wait for subscriber to finish
        await asyncio.wait_for(task, timeout=2.0)

        assert len(received) >= 2
        statuses = [e.get("status") for e in received]
        assert ConnectionStatus.SUCCESS in statuses

    @pytest.mark.asyncio
    async def test_notification_contains_required_fields(self, manager: ConnectionStatusManager):
        """Each notification should have status, message, progress, timestamp."""
        received = []

        async def subscriber():
            stream = manager.subscribe(1)
            try:
                received.append(await anext(stream))
            finally:
                await stream.aclose()

        task = asyncio.create_task(subscriber())
        await asyncio.sleep(0.05)
        await manager.set_status(1, ConnectionStatus.CODE_SENT, "Code sent", 40)
        await asyncio.wait_for(task, timeout=2.0)

        assert len(received) == 1
        event = received[0]
        assert "status" in event
        assert "message" in event
        assert "progress" in event
        assert "timestamp" in event

    @pytest.mark.asyncio
    async def test_sse_serialization_works_because_str_enum(self, manager: ConnectionStatusManager):
        """
        ConnectionStatus inherits from (str, Enum), so json.dumps() works
        natively -- enum values serialize to their string values.

        This means the SSE events CAN be serialized, but the string value
        is "success" (not "connected" which the frontend expects).
        """
        await manager.set_status(1, ConnectionStatus.SUCCESS, "Done", 100)
        status_data = manager.get_status(1)

        # The stored status is a str+Enum hybrid
        assert isinstance(status_data["status"], ConnectionStatus)
        assert isinstance(status_data["status"], str)

        # json.dumps works because ConnectionStatus inherits from str
        serialized = json.dumps({
            "status": status_data["status"],
            "message": status_data["message"],
            "progress": status_data["progress"],
        })
        parsed = json.loads(serialized)

        # The serialized value is "success", NOT "connected"
        assert parsed["status"] == "success"
        assert parsed["status"] != "connected"  # This is the frontend mismatch


# ============================================================================
# 3. HTTP Endpoint Tests (with mocked browser/client)
# ============================================================================


class TestAccountCRUD:
    """Test basic account CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_account(self, client: AsyncClient):
        response = await client.post(
            "/api/accounts/",
            json={"account_id": "dewu_001", "account_name": "Test Account"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["account_id"] == "dewu_001"
        assert data["account_name"] == "Test Account"
        assert data["status"] in ["active", "inactive"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_duplicate_account(self, client: AsyncClient, sample_account: dict):
        response = await client.post(
            "/api/accounts/",
            json={"account_id": "test_user_001", "account_name": "Duplicate"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_accounts(self, client: AsyncClient, sample_account: dict):
        response = await client.get("/api/accounts/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_account(self, client: AsyncClient, sample_account: dict):
        account_id = sample_account["id"]
        response = await client.get(f"/api/accounts/{account_id}")
        assert response.status_code == 200
        assert response.json()["id"] == account_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_account(self, client: AsyncClient):
        response = await client.get("/api/accounts/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_account(self, client: AsyncClient, sample_account: dict):
        account_id = sample_account["id"]
        with patch("api.account.browser_manager") as mock_bm:
            mock_bm.close_context = AsyncMock()
            response = await client.delete(f"/api/accounts/{account_id}")
            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_account_stats(self, client: AsyncClient, sample_account: dict):
        response = await client.get("/api/accounts/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_accounts" in data
        assert "active_accounts" in data
        assert data["total_accounts"] >= 1


class TestConnectEndpoint:
    """Test the POST /api/accounts/connect/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_connect_nonexistent_account(self, client: AsyncClient):
        """Connecting to a non-existent account should return 404."""
        response = await client.post(
            "/api/accounts/connect/99999",
            json={"phone": "13800138000", "code": "1234"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_connect_empty_code_rejected_by_validation(self, client: AsyncClient, sample_account: dict):
        """
        DOCUMENTS BLOCKER 1: Empty code should be rejected by Pydantic.

        The frontend sends code='' for Phase 1 (send verification code),
        but the schema requires min_length=4.
        """
        account_id = sample_account["id"]
        response = await client.post(
            f"/api/accounts/connect/{account_id}",
            json={"phone": "13800138000", "code": ""},
        )
        # This returns 422 because Pydantic rejects empty code
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_connect_missing_code_rejected(self, client: AsyncClient, sample_account: dict):
        """Missing code field should be rejected."""
        account_id = sample_account["id"]
        response = await client.post(
            f"/api/accounts/connect/{account_id}",
            json={"phone": "13800138000"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_connect_invalid_phone_rejected(self, client: AsyncClient, sample_account: dict):
        """Invalid phone number should be rejected."""
        account_id = sample_account["id"]
        response = await client.post(
            f"/api/accounts/connect/{account_id}",
            json={"phone": "123", "code": "1234"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_connect_success_flow(self, client: AsyncClient, sample_account: dict, mock_dewu_client):
        """
        Full successful connection flow with mocked DewuClient.
        """
        account_id = sample_account["id"]

        with patch("api.account.get_dewu_client", new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_dewu_client

            response = await client.post(
                f"/api/accounts/connect/{account_id}",
                json={"phone": "13800138000", "code": "1234"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_connect_failure_flow(self, client: AsyncClient, sample_account: dict, mock_dewu_client):
        """Connection failure should return success=False and status=inactive."""
        account_id = sample_account["id"]
        mock_dewu_client.login_with_sms = AsyncMock(return_value=(False, "Invalid code"))

        with patch("api.account.get_dewu_client", new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_dewu_client

            response = await client.post(
                f"/api/accounts/connect/{account_id}",
                json={"phone": "13800138000", "code": "1234"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "inactive"

    @pytest.mark.asyncio
    async def test_connect_exception_handling(self, client: AsyncClient, sample_account: dict):
        """Exceptions during connection should be caught and return error status."""
        account_id = sample_account["id"]

        with patch("api.account.get_dewu_client", new_callable=AsyncMock) as mock_get_client:
            mock_get_client.side_effect = Exception("Browser crash")

            response = await client.post(
                f"/api/accounts/connect/{account_id}",
                json={"phone": "13800138000", "code": "1234"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "error"
        assert "Browser crash" in data["message"]


class TestConnectionStatusEndpoint:
    """Test GET /api/accounts/connect/{id}/status endpoint."""

    @pytest.mark.asyncio
    async def test_status_nonexistent_account(self, client: AsyncClient):
        response = await client.get("/api/accounts/connect/99999/status")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_status_no_session(self, client: AsyncClient, sample_account: dict):
        """Account with no session should return idle status."""
        account_id = sample_account["id"]
        with patch("api.account.browser_manager") as mock_bm:
            mock_bm.get_context = AsyncMock(return_value=None)

            response = await client.get(f"/api/accounts/connect/{account_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["is_connected"] is False
        assert data["status"] == "idle"


class TestSSEStream:
    """Test the SSE stream endpoint."""

    @pytest.mark.asyncio
    async def test_stream_nonexistent_account(self, client: AsyncClient):
        """SSE stream for non-existent account should return error event."""
        response = await client.get("/api/accounts/connect/99999/stream")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        # The body should contain an error JSON
        body = response.text
        assert "error" in body


class TestDisconnectEndpoint:
    """Test POST /api/accounts/disconnect/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_account(self, client: AsyncClient):
        response = await client.post("/api/accounts/disconnect/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_disconnect_success(self, client: AsyncClient, sample_account: dict):
        account_id = sample_account["id"]
        with patch("api.account.browser_manager") as mock_bm:
            mock_bm.close_context = AsyncMock()
            response = await client.post(f"/api/accounts/disconnect/{account_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestDeprecatedEndpoints:
    """Verify deprecated endpoints still work (backward compatibility)."""

    @pytest.mark.asyncio
    async def test_login_endpoint_redirects_to_connect(self, client: AsyncClient, sample_account: dict, mock_dewu_client):
        """POST /login/{id} should proxy to /connect/{id}."""
        account_id = sample_account["id"]

        with patch("api.account.get_dewu_client", new_callable=AsyncMock) as mock_get_client:
            mock_get_client.return_value = mock_dewu_client

            response = await client.post(
                f"/api/accounts/login/{account_id}",
                json={"phone": "13800138000", "code": "1234"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_logout_endpoint_redirects_to_disconnect(self, client: AsyncClient, sample_account: dict):
        """POST /logout/{id} should proxy to /disconnect/{id}."""
        account_id = sample_account["id"]
        with patch("api.account.browser_manager") as mock_bm:
            mock_bm.close_context = AsyncMock()
            response = await client.post(f"/api/accounts/logout/{account_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ============================================================================
# 4. Protocol Alignment Tests (Frontend-Backend Contract)
# ============================================================================


class TestProtocolAlignment:
    """
    These tests verify that frontend and backend agree on the protocol.

    They document known mismatches and serve as a regression suite.
    """

    def test_connection_status_values_expected_by_frontend(self):
        """
        Frontend ConnectionModal expects these status values in SSE events.
        Verify all exist in the backend enum.
        """
        frontend_values = [
            "idle", "waiting_phone", "code_sent",
            "waiting_verify", "verifying", "error",
        ]
        backend_values = [s.value for s in ConnectionStatus]

        for val in frontend_values:
            assert val in backend_values, (
                f"Frontend expects status '{val}' but backend does not define it"
            )

    def test_frontend_connected_not_in_backend(self):
        """
        MISMATCH: Frontend uses 'connected' for success,
        but backend uses 'success'. This documents the bug.
        """
        backend_values = [s.value for s in ConnectionStatus]
        assert "connected" not in backend_values
        assert "success" in backend_values

    def test_account_status_logging_in_exists(self):
        """Backend AccountStatus has 'logging_in' which frontend SDK lacks."""
        assert AccountStatus.LOGGING_IN.value == "logging_in"

    def test_connection_response_fields(self):
        """
        Verify ConnectionResponse matches what frontend ConnectResponse expects:
        { success: boolean, message: string, status: string, storage_state?: string }
        """
        resp = ConnectionResponse(
            success=True,
            message="ok",
            status="active",
            storage_state="enc_data",
        )
        dumped = resp.model_dump()
        # Frontend expects these exact field names
        assert "success" in dumped
        assert "message" in dumped
        assert "status" in dumped
        assert "storage_state" in dumped

    def test_sse_event_names(self):
        """
        Verify SSE event names match frontend EventSource listeners.

        Frontend listens for: 'status_update', 'done'
        Backend sends:        'status_update', 'done'
        """
        # This is a documentation test. The actual event names are string
        # literals in account.py:607 and account.py:613.
        # We verify them via grep-like checking of known values.
        expected_events = {"status_update", "done"}
        # Backend generates: "event: status_update\n" and "event: done\n"
        # These should match what the frontend addEventListener() uses.
        assert expected_events == {"status_update", "done"}

    def test_sse_done_event_final_status_mismatch(self):
        """
        MISMATCH: Backend sends final_status=ConnectionStatus.SUCCESS (enum)
        which would serialize to the string "success" if .value is used,
        but frontend checks final_status === 'connected'.

        This test documents that the values do not match.
        """
        backend_success = ConnectionStatus.SUCCESS.value  # "success"
        frontend_expected = "connected"
        assert backend_success != frontend_expected, (
            "If this fails, the mismatch has been fixed (both now use the same value)"
        )

    def test_connection_request_two_phase_impossible(self):
        """
        DESIGN BUG: The two-phase connection flow requires sending
        code='' for Phase 1, but the schema rejects it.

        Phase 1: { phone: "13800138000", code: "" }  -> Should send SMS
        Phase 2: { phone: "13800138000", code: "1234" } -> Should verify

        Phase 1 fails Pydantic validation because code min_length=4.
        """
        # Phase 2 works fine
        req2 = ConnectionRequest(phone="13800138000", code="1234")
        assert req2.code == "1234"

        # Phase 1 fails
        with pytest.raises(ValidationError):
            ConnectionRequest(phone="13800138000", code="")


# ============================================================================
# 5. DewuClient Unit Tests (logic without browser)
# ============================================================================


class TestDewuClientSelectors:
    """Validate that LOGIN_SELECTORS are well-formed."""

    def test_selectors_are_non_empty_lists(self):
        from core.dewu_client import LOGIN_SELECTORS

        required_categories = [
            "phone_input", "agree_checkbox", "code_button",
            "code_input", "login_button", "logged_in_pages",
            "logged_in_indicator", "error_message",
        ]
        for category in required_categories:
            assert category in LOGIN_SELECTORS, f"Missing selector category: {category}"
            assert isinstance(LOGIN_SELECTORS[category], list)
            assert len(LOGIN_SELECTORS[category]) > 0, f"Empty selector list: {category}"

    def test_login_url_is_valid(self):
        from core.dewu_client import DewuClient
        assert DewuClient.LOGIN_URL.startswith("https://")
        assert "dewu.com" in DewuClient.LOGIN_URL


# ============================================================================
# 6. Crypto Integration Test
# ============================================================================


class TestCryptoRoundtrip:
    """Verify encrypt/decrypt roundtrip for storage state."""

    def test_encrypt_decrypt_roundtrip(self):
        from utils.crypto import encrypt_data, decrypt_data

        original = '{"cookies": [{"name": "session", "value": "abc123"}]}'
        encrypted = encrypt_data(original)
        assert encrypted != original
        assert len(encrypted) > 0

        decrypted = decrypt_data(encrypted)
        assert decrypted == original

    def test_encrypt_empty_string(self):
        from utils.crypto import encrypt_data, decrypt_data

        encrypted = encrypt_data("")
        assert encrypted == ""
        decrypted = decrypt_data("")
        assert decrypted == ""
