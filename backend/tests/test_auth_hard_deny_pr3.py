"""
Step 4 PR3 tests: Propagate revoke and device-mismatch truth through local session updates.

PR3 Goals:
- Ensure remote hard-deny outcomes reach local machine-session truth promptly
- Tighten login/refresh/me error handling for hard-deny states
- Confirm revoke remains more authoritative than grace
- Scheduler/poller runtime checks see hard-deny states
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.auth_dependencies import (
    RUNTIME_HARD_STOP_STATES,
    get_runtime_auth_failure_reason,
    is_runtime_hard_stop_state,
)
from core.device_identity import FileDeviceIdentityStore
from core.remote_auth_client import RemoteAuthResponseError
from core.secret_store import FileSecretStore
from models import Base, RemoteAuthSession
from schemas.auth import RemoteAuthSessionPayload, RemoteAuthUser
from services.auth_service import ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, AuthService


class DummyRemoteAuthClient:
    """Mock remote auth client for testing."""

    def __init__(
        self,
        *,
        login_result=None,
        refresh_result=None,
        me_result=None,
        login_exc=None,
        refresh_exc=None,
        me_exc=None,
    ) -> None:
        self.login_result = login_result
        self.refresh_result = refresh_result
        self.me_result = me_result
        self.login_exc = login_exc
        self.refresh_exc = refresh_exc
        self.me_exc = me_exc

    async def login(self, **kwargs):
        if self.login_exc:
            raise self.login_exc
        return self.login_result

    async def refresh(self, **kwargs):
        if self.refresh_exc:
            raise self.refresh_exc
        return self.refresh_result

    async def me(self, **kwargs):
        if self.me_exc:
            raise self.me_exc
        return self.me_result

    async def aclose(self) -> None:
        return None


def _session_payload(
    *,
    access_token: str = "access-token",
    refresh_token: str = "refresh-token",
    expires_at: datetime | None = None,
    offline_grace_until: datetime | None = None,
    device_id: str = "device-1",
) -> RemoteAuthSessionPayload:
    return RemoteAuthSessionPayload(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at or datetime(2026, 4, 20, 10, 0, 0),
        token_type="Bearer",
        user=RemoteAuthUser(
            id="u_123",
            username="alice",
            display_name="Alice",
            tenant_id="tenant_1",
        ),
        license_status="active",
        entitlements=["dashboard:view"],
        device_id=device_id,
        device_status="bound",
        offline_grace_until=offline_grace_until,
        minimum_supported_version="0.2.0",
    )


@pytest_asyncio.fixture()
async def auth_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def temp_secret_store(tmp_path):
    return FileSecretStore(path=tmp_path / "secrets.json")


@pytest_asyncio.fixture()
async def temp_device_store(tmp_path):
    return FileDeviceIdentityStore(path=tmp_path / "device.json")


class TestHardDenyPropagation:
    """PR3: Hard-deny outcomes propagate to local session tests."""

    @pytest.mark.asyncio
    async def test_login_revoked_sets_revoked_state(self, auth_db_session, tmp_path):
        """Remote revoked response during login sets local session to revoked."""
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            login_exc=RemoteAuthResponseError(
                error_code="revoked",
                message="Account revoked",
                status_code=403,
            )
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.login(
                username="alice",
                password="secret",
                device_id="device-1",
                client_version="0.2.0",
            )

        # Verify session state after rejection
        summary = await service.get_session_summary()
        assert summary.auth_state == "revoked"
        assert summary.denial_reason == "revoked"

    @pytest.mark.asyncio
    async def test_login_disabled_sets_revoked_state(self, auth_db_session, tmp_path):
        """Remote disabled response during login sets local session to revoked."""
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            login_exc=RemoteAuthResponseError(
                error_code="disabled",
                message="Account disabled",
                status_code=403,
            )
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.login(
                username="alice",
                password="secret",
                device_id="device-1",
                client_version="0.2.0",
            )

        summary = await service.get_session_summary()
        assert summary.auth_state == "revoked"
        assert summary.denial_reason == "disabled"

    @pytest.mark.asyncio
    async def test_login_device_mismatch_sets_device_mismatch_state(self, auth_db_session, tmp_path):
        """Remote device_mismatch response during login sets local session to device_mismatch."""
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            login_exc=RemoteAuthResponseError(
                error_code="device_mismatch",
                message="Device not bound",
                status_code=403,
            )
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.login(
                username="alice",
                password="secret",
                device_id="device-1",
                client_version="0.2.0",
            )

        summary = await service.get_session_summary()
        assert summary.auth_state == "device_mismatch"
        assert summary.denial_reason == "device_mismatch"

    @pytest.mark.asyncio
    async def test_refresh_revoked_sets_revoked_state(self, auth_db_session, tmp_path):
        """Remote revoked response during refresh sets local session to revoked."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="refresh_required",
            remote_user_id="u_123",
            expires_at=now - timedelta(minutes=5),
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            refresh_exc=RemoteAuthResponseError(
                error_code="revoked",
                message="Token revoked",
                status_code=403,
            )
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.refresh_if_needed(client_version="0.2.0")

        summary = await service.get_session_summary()
        assert summary.auth_state == "revoked"
        assert summary.denial_reason == "revoked"

    @pytest.mark.asyncio
    async def test_refresh_device_mismatch_sets_device_mismatch_state(self, auth_db_session, tmp_path):
        """Remote device_mismatch response during refresh sets local session to device_mismatch."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="refresh_required",
            remote_user_id="u_123",
            expires_at=now - timedelta(minutes=5),
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            refresh_exc=RemoteAuthResponseError(
                error_code="device_mismatch",
                message="Device mismatch",
                status_code=403,
            )
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.refresh_if_needed(client_version="0.2.0")

        summary = await service.get_session_summary()
        assert summary.auth_state == "device_mismatch"
        assert summary.denial_reason == "device_mismatch"

    @pytest.mark.asyncio
    async def test_me_revoked_sets_revoked_state(self, auth_db_session, tmp_path):
        """Remote revoked response during /me sets local session to revoked."""
        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(ACCESS_TOKEN_KEY, "valid-access")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            me_exc=RemoteAuthResponseError(
                error_code="revoked",
                message="Token revoked",
                status_code=401,
            )
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.get_me()

        summary = await service.get_session_summary()
        assert summary.auth_state == "revoked"
        assert summary.denial_reason == "revoked"


class TestRevokePrecedenceOverGrace:
    """PR3: Revoke takes precedence over grace tests."""

    @pytest.mark.asyncio
    async def test_revoke_overrides_grace_window(self, auth_db_session, tmp_path):
        """Revoked state takes precedence over valid grace window."""
        now = datetime.now(UTC).replace(tzinfo=None)
        # Session in grace with valid window
        session = RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            offline_grace_until=now + timedelta(hours=1),  # Still valid
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(ACCESS_TOKEN_KEY, "valid-access")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # But /me returns revoked
        dummy_client = DummyRemoteAuthClient(
            me_exc=RemoteAuthResponseError(
                error_code="revoked",
                message="Token revoked",
                status_code=401,
            )
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.get_me()

        # Should be revoked, not grace
        summary = await service.get_session_summary()
        assert summary.auth_state == "revoked"
        assert summary.denial_reason == "revoked"

    @pytest.mark.asyncio
    async def test_device_mismatch_overrides_grace_window(self, auth_db_session, tmp_path):
        """Device mismatch takes precedence over valid grace window."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            offline_grace_until=now + timedelta(hours=1),
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(ACCESS_TOKEN_KEY, "valid-access")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            me_exc=RemoteAuthResponseError(
                error_code="device_mismatch",
                message="Device mismatch",
                status_code=403,
            )
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.get_me()

        summary = await service.get_session_summary()
        assert summary.auth_state == "device_mismatch"
        assert summary.denial_reason == "device_mismatch"


class TestRuntimeHardStopStates:
    """PR3: Runtime hard-stop state detection tests."""

    def test_revoked_is_hard_stop_state(self):
        """Revoked state is recognized as hard-stop."""
        assert is_runtime_hard_stop_state("revoked")
        assert "revoked" in RUNTIME_HARD_STOP_STATES

    def test_device_mismatch_is_hard_stop_state(self):
        """Device mismatch is recognized as hard-stop."""
        assert is_runtime_hard_stop_state("device_mismatch")
        assert "device_mismatch" in RUNTIME_HARD_STOP_STATES

    def test_expired_is_hard_stop_state(self):
        """Expired state is recognized as hard-stop."""
        assert is_runtime_hard_stop_state("expired")
        assert "expired" in RUNTIME_HARD_STOP_STATES

    def test_grace_is_not_hard_stop_state(self):
        """Grace state is NOT a hard-stop."""
        assert not is_runtime_hard_stop_state("authenticated_grace")
        assert "authenticated_grace" not in RUNTIME_HARD_STOP_STATES

    def test_active_is_not_hard_stop_state(self):
        """Active state is NOT a hard-stop."""
        assert not is_runtime_hard_stop_state("authenticated_active")
        assert "authenticated_active" not in RUNTIME_HARD_STOP_STATES

    def test_revoked_failure_reason(self):
        """Revoked state returns correct failure reason."""
        from schemas.auth import LocalAuthSessionSummary
        summary = LocalAuthSessionSummary(
            auth_state="revoked",
            denial_reason="revoked",
        )
        reason = get_runtime_auth_failure_reason(summary)
        assert reason == "remote_auth_revoked"

    def test_device_mismatch_failure_reason(self):
        """Device mismatch state returns correct failure reason."""
        from schemas.auth import LocalAuthSessionSummary
        summary = LocalAuthSessionSummary(
            auth_state="device_mismatch",
            denial_reason="device_mismatch",
        )
        reason = get_runtime_auth_failure_reason(summary)
        assert reason == "remote_auth_device_mismatch"
