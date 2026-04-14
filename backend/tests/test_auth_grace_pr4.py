"""
Step 4 PR4 tests: Hardened offline grace lifecycle and startup/runtime revalidation strategy.

PR4 Goals:
- Grace-window evaluation at startup and after refresh/network failure
- Revalidation timing/trigger strategy for active/grace/expired transitions
- Runtime revalidation for scheduler/poller
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.device_identity import FileDeviceIdentityStore
from core.remote_auth_client import RemoteAuthTransportError
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


class TestStartupGraceEvaluation:
    """PR4: Startup grace-window evaluation tests."""

    @pytest.mark.asyncio
    async def test_startup_in_grace_returns_grace(self, auth_db_session, tmp_path):
        """Startup with valid grace window returns authenticated_grace."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            offline_grace_until=now + timedelta(hours=1),  # Valid grace
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            now_fn=lambda: now,
        )

        result = await service.restore_session()

        assert result.auth_state == "authenticated_grace"

    @pytest.mark.asyncio
    async def test_startup_grace_expired_returns_expired(self, auth_db_session, tmp_path):
        """Startup with expired grace window returns expired."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            offline_grace_until=now - timedelta(minutes=1),  # Expired grace
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            now_fn=lambda: now,
        )

        result = await service.restore_session()

        assert result.auth_state == "expired"
        assert result.denial_reason == "offline_grace_expired"


class TestRefreshNetworkFailureGrace:
    """PR4: Refresh network failure grace entry vs expired tests."""

    @pytest.mark.asyncio
    async def test_network_failure_enters_grace_when_within_window(self, auth_db_session, tmp_path):
        """Network failure enters grace when within grace window."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="refresh_required",
            remote_user_id="u_123",
            expires_at=now - timedelta(minutes=5),  # Expired
            offline_grace_until=now + timedelta(hours=1),  # Valid grace window
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            refresh_exc=RemoteAuthTransportError("timeout")
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")

        # Should enter grace, not expired
        assert result.auth_state == "authenticated_grace"
        assert result.denial_reason == "network_timeout"

    @pytest.mark.asyncio
    async def test_network_failure_expires_when_outside_window(self, auth_db_session, tmp_path):
        """Network failure expires when outside grace window."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="refresh_required",
            remote_user_id="u_123",
            expires_at=now - timedelta(minutes=5),
            offline_grace_until=now - timedelta(minutes=1),  # Expired grace window
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            refresh_exc=RemoteAuthTransportError("timeout")
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")

        # Should expire, not grace
        assert result.auth_state == "expired"
        assert result.denial_reason == "network_timeout"


class TestRuntimeRevalidation:
    """PR4: Runtime revalidation strategy tests."""

    @pytest.mark.asyncio
    async def test_explicit_revalidation_triggers_refresh(self, auth_db_session, tmp_path):
        """Explicit revalidation triggers refresh when token near expiry."""
        now = datetime.now(UTC).replace(tzinfo=None)
        # Token expires in 3 minutes (within proactive buffer)
        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            expires_at=now + timedelta(minutes=3),
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        new_payload = _session_payload(
            access_token="new-access",
            refresh_token="new-refresh",
            expires_at=now + timedelta(hours=1),
        )
        dummy_client = DummyRemoteAuthClient(refresh_result=new_payload)

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        # Call refresh_if_needed as explicit revalidation
        result = await service.refresh_if_needed(client_version="0.2.0")

        assert result.auth_state == "authenticated_active"
        # Token should be refreshed
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) == "new-access"

    @pytest.mark.asyncio
    async def test_explicit_revalidation_preserves_grace(self, auth_db_session, tmp_path):
        """Explicit revalidation preserves grace when network fails."""
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
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            now_fn=lambda: now,
        )

        # Revalidation should preserve grace
        result = await service.refresh_if_needed(client_version="0.2.0")

        assert result.auth_state == "authenticated_grace"


class TestGraceTransitions:
    """PR4: Grace state transition tests."""

    @pytest.mark.asyncio
    async def test_active_to_grace_transition(self, auth_db_session, tmp_path):
        """Active session transitions to grace on network failure."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="refresh_required",
            remote_user_id="u_123",
            expires_at=now - timedelta(minutes=5),
            offline_grace_until=now + timedelta(hours=1),
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(
            refresh_exc=RemoteAuthTransportError("timeout")
        )

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")

        assert result.auth_state == "authenticated_grace"

    @pytest.mark.asyncio
    async def test_grace_to_expired_transition(self, auth_db_session, tmp_path):
        """Grace session transitions to expired when window closes."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            offline_grace_until=now - timedelta(minutes=1),  # Expired
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            now_fn=lambda: now,
        )

        result = await service.restore_session()

        assert result.auth_state == "expired"

    @pytest.mark.asyncio
    async def test_grace_to_active_on_successful_refresh(self, auth_db_session, tmp_path):
        """Grace session transitions to active on successful refresh."""
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
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        new_payload = _session_payload(
            access_token="new-access",
            refresh_token="new-refresh",
            expires_at=now + timedelta(hours=1),
        )
        dummy_client = DummyRemoteAuthClient(refresh_result=new_payload)

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")

        assert result.auth_state == "authenticated_active"


class TestGraceDoesNotOutrankHardDeny:
    """PR4: Grace does not outrank hard-deny tests."""

    @pytest.mark.asyncio
    async def test_revoke_takes_precedence_over_grace(self, auth_db_session, tmp_path):
        """Revoke takes precedence over grace even with valid window."""
        now = datetime.now(UTC).replace(tzinfo=None)
        # Start in grace with valid window
        session = RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            offline_grace_until=now + timedelta(hours=1),
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        from core.remote_auth_client import RemoteAuthResponseError
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

        # Should be revoked, not grace
        summary = await service.get_session_summary()
        assert summary.auth_state == "revoked"
