"""
Step 1 / PR5 tests for local auth API surface.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import api.auth as auth_api
from core.auth_events import auth_event_emitter
from core.remote_auth_client import RemoteAuthResponseError, RemoteAuthTransportError


class DummyAuthService:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def login(self, **kwargs):
        return {
            "auth_state": "authenticated_active",
            "remote_user_id": "u_123",
            "display_name": "Alice",
            "license_status": "active",
            "entitlements": ["dashboard:view"],
            "expires_at": "2026-04-20T10:00:00",
            "last_verified_at": "2026-04-14T00:00:00",
            "offline_grace_until": "2026-04-21T10:00:00",
            "denial_reason": None,
            "device_id": kwargs["device_id"],
        }

    async def refresh_if_needed(self, **kwargs):
        return {
            "auth_state": "authenticated_active",
            "remote_user_id": "u_123",
            "display_name": "Alice",
            "license_status": "active",
            "entitlements": ["dashboard:view"],
            "expires_at": "2026-04-20T11:00:00",
            "last_verified_at": "2026-04-14T00:10:00",
            "offline_grace_until": "2026-04-21T10:00:00",
            "denial_reason": None,
            "device_id": "device-1",
        }

    async def logout(self):
        return {
            "auth_state": "unauthenticated",
            "remote_user_id": None,
            "display_name": None,
            "license_status": None,
            "entitlements": [],
            "expires_at": None,
            "last_verified_at": None,
            "offline_grace_until": None,
            "denial_reason": None,
            "device_id": None,
        }

    async def get_session_summary(self):
        return {
            "auth_state": "authenticated_grace",
            "remote_user_id": "u_123",
            "display_name": "Alice",
            "license_status": "active",
            "entitlements": ["dashboard:view"],
            "expires_at": "2026-04-20T11:00:00",
            "last_verified_at": "2026-04-14T00:10:00",
            "offline_grace_until": "2026-04-21T10:00:00",
            "denial_reason": "network_timeout",
            "device_id": "device-1",
        }

    async def get_me(self):
        return {
            "user": {
                "id": "u_123",
                "username": "alice",
                "display_name": "Alice",
                "tenant_id": "tenant_1",
            },
            "license_status": "active",
            "entitlements": ["dashboard:view"],
            "device_id": "device-1",
            "device_status": "bound",
            "offline_grace_until": "2026-04-21T10:00:00",
            "minimum_supported_version": "0.2.0",
        }


@pytest.fixture()
def restore_auth_service_builder():
    original = auth_api.build_auth_service
    yield
    auth_api.build_auth_service = original


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_auth_login(self, client: AsyncClient, restore_auth_service_builder) -> None:
        auth_api.build_auth_service = lambda db: DummyAuthService()

        response = await client.post(
            "/api/auth/login",
            json={
                "username": "alice",
                "password": "secret",
                "device_id": "device-1",
                "client_version": "0.2.0",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["auth_state"] == "authenticated_active"
        assert data["device_id"] == "device-1"

    @pytest.mark.asyncio
    async def test_auth_refresh(self, client: AsyncClient, restore_auth_service_builder) -> None:
        auth_api.build_auth_service = lambda db: DummyAuthService()

        response = await client.post(
            "/api/auth/refresh",
            json={"client_version": "0.2.0"},
        )

        assert response.status_code == 200
        assert response.json()["auth_state"] == "authenticated_active"

    @pytest.mark.asyncio
    async def test_auth_logout(self, client: AsyncClient, restore_auth_service_builder) -> None:
        auth_api.build_auth_service = lambda db: DummyAuthService()

        response = await client.post("/api/auth/logout")

        assert response.status_code == 200
        assert response.json()["auth_state"] == "unauthenticated"

    @pytest.mark.asyncio
    async def test_auth_session(self, client: AsyncClient, restore_auth_service_builder) -> None:
        auth_api.build_auth_service = lambda db: DummyAuthService()

        response = await client.get("/api/auth/session")

        assert response.status_code == 200
        assert response.json()["auth_state"] == "authenticated_grace"

    @pytest.mark.asyncio
    async def test_auth_session_uses_real_auth_service(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/session")

        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_state"] == "authenticated_active"
        assert payload["remote_user_id"] == "test-user"
        assert payload["device_id"] == "test-device"

    @pytest.mark.asyncio
    async def test_auth_me(self, client: AsyncClient, restore_auth_service_builder) -> None:
        auth_api.build_auth_service = lambda db: DummyAuthService()

        response = await client.get("/api/auth/me")

        assert response.status_code == 200
        assert response.json()["user"]["id"] == "u_123"

    @pytest.mark.asyncio
    async def test_auth_route_maps_remote_response_error(self, client: AsyncClient, restore_auth_service_builder) -> None:
        class RevokedAuthService(DummyAuthService):
            async def refresh_if_needed(self, **kwargs):
                raise RemoteAuthResponseError("revoked", "revoked", status_code=403, details={})

        auth_api.build_auth_service = lambda db: RevokedAuthService()

        response = await client.post("/api/auth/refresh", json={"client_version": "0.2.0"})

        assert response.status_code == 403
        payload = response.json()["detail"]
        assert payload["error_code"] == "revoked"

    @pytest.mark.asyncio
    async def test_auth_route_maps_transport_error(self, client: AsyncClient, restore_auth_service_builder) -> None:
        class TimeoutAuthService(DummyAuthService):
            async def get_me(self):
                raise RemoteAuthTransportError("timeout")

        auth_api.build_auth_service = lambda db: TimeoutAuthService()

        response = await client.get("/api/auth/me")

        assert response.status_code == 503
        payload = response.json()["detail"]
        assert payload["error_code"] == "network_timeout"

    @pytest.mark.asyncio
    async def test_auth_route_injects_trace_context_into_emitted_events(
        self,
        client: AsyncClient,
        restore_auth_service_builder,
    ) -> None:
        class EmittingAuthService(DummyAuthService):
            async def login(self, **kwargs):
                auth_event_emitter.login_succeeded(
                    remote_user_id="u_123",
                    device_id=kwargs["device_id"],
                    auth_state="authenticated_active",
                )
                return await super().login(**kwargs)

        auth_event_emitter.start_capture()
        auth_api.build_auth_service = lambda db: EmittingAuthService()

        response = await client.post(
            "/api/auth/login",
            headers={"X-Request-ID": "req-123"},
            json={
                "username": "alice",
                "password": "secret",
                "device_id": "device-1",
                "client_version": "0.2.0",
            },
        )

        events = auth_event_emitter.stop_capture()
        assert response.status_code == 200
        assert response.headers["X-Trace-ID"] == "req-123"
        assert response.headers["X-Request-ID"] == "req-123"
        assert len(events) == 1
        assert events[0].trace_id == "req-123"
        assert events[0].request_id == "req-123"
        assert events[0].route_name == "login_auth"
        assert events[0].method == "POST"
        assert events[0].path == "/api/auth/login"

    @pytest.mark.asyncio
    async def test_auth_route_generates_trace_id_when_header_missing(
        self,
        client: AsyncClient,
        restore_auth_service_builder,
    ) -> None:
        class EmittingAuthService(DummyAuthService):
            async def refresh_if_needed(self, **kwargs):
                auth_event_emitter.refresh_started(
                    remote_user_id="u_123",
                    device_id="device-1",
                )
                return await super().refresh_if_needed(**kwargs)

        auth_event_emitter.start_capture()
        auth_api.build_auth_service = lambda db: EmittingAuthService()

        response = await client.post(
            "/api/auth/refresh",
            json={"client_version": "0.2.0"},
        )

        events = auth_event_emitter.stop_capture()
        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers
        assert response.headers["X-Trace-ID"]
        assert "X-Request-ID" not in response.headers
        assert len(events) == 1
        assert events[0].trace_id == response.headers["X-Trace-ID"]
        assert events[0].request_id is None
        assert events[0].route_name == "refresh_auth"
