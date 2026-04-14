"""
Step 4 PR5: End-to-end auth lifecycle proof pack.

This module provides integration tests proving Step 4 lifecycle correctness
end-to-end: startup restore, refresh rotation, hard-deny propagation, and grace-window semantics.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.device_identity import FileDeviceIdentityStore
from core.remote_auth_client import RemoteAuthResponseError, RemoteAuthTransportError
from core.secret_store import FileSecretStore
from models import Base, RemoteAuthSession
from schemas.auth import RemoteAuthSessionPayload, RemoteAuthUser
from services.auth_service import ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, AuthService


class DummyRemoteAuthClient:
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


class TestStep4EndToEndProof:
    """Step 4 end-to-end lifecycle proof pack."""

    @pytest.mark.asyncio
    async def test_full_lifecycle_login_refresh_logout(self, auth_db_session, tmp_path):
        """E2E: Login -> Refresh -> Logout lifecycle."""
        now = datetime.now(UTC).replace(tzinfo=None)
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # Login
        login_payload = _session_payload(
            access_token="access-1",
            refresh_token="refresh-1",
            expires_at=now + timedelta(minutes=3),
            device_id="device-1",
        )
        client = DummyRemoteAuthClient(login_result=login_payload)
        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: client,
            now_fn=lambda: now,
        )

        result = await service.login(
            username="alice",
            password="secret",
            device_id="device-1",
            client_version="0.2.0",
        )
        assert result.auth_state == "authenticated_active"
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) == "access-1"

        # Refresh (proactive)
        refresh_payload = _session_payload(
            access_token="access-2",
            refresh_token="refresh-2",
            expires_at=now + timedelta(hours=1),
            device_id="device-1",
        )
        client = DummyRemoteAuthClient(refresh_result=refresh_payload)
        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: client,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")
        assert result.auth_state == "authenticated_active"
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) == "access-2"

        # Logout
        result = await service.logout()
        assert result.auth_state == "unauthenticated"
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) is None

    @pytest.mark.asyncio
    async def test_full_lifecycle_grace_recovery(self, auth_db_session, tmp_path):
        """E2E: Active -> Network Failure -> Grace -> Recovery lifecycle."""
        now = datetime.now(UTC).replace(tzinfo=None)
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # Setup active session
        session = RemoteAuthSession(
            auth_state="refresh_required",
            remote_user_id="u_123",
            expires_at=now - timedelta(minutes=5),
            offline_grace_until=now + timedelta(hours=1),
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")

        # Network failure enters grace
        client = DummyRemoteAuthClient(
            refresh_exc=RemoteAuthTransportError("timeout")
        )
        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: client,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")
        assert result.auth_state == "authenticated_grace"

        # Recovery to active
        recovery_payload = _session_payload(
            access_token="access-recovered",
            refresh_token="refresh-recovered",
            expires_at=now + timedelta(minutes=3),
            device_id="device-1",
        )
        client = DummyRemoteAuthClient(refresh_result=recovery_payload)
        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: client,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")
        assert result.auth_state == "authenticated_active"
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) == "access-recovered"

    @pytest.mark.asyncio
    async def test_full_lifecycle_hard_deny_from_grace(self, auth_db_session, tmp_path):
        """E2E: Grace -> Revoked (hard-deny priority) lifecycle."""
        now = datetime.now(UTC).replace(tzinfo=None)
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # Setup grace session
        session = RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            offline_grace_until=now + timedelta(hours=1),  # Valid grace
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")

        # Revoked during refresh attempt
        client = DummyRemoteAuthClient(
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
            remote_client_factory=lambda: client,
            now_fn=lambda: now,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.refresh_if_needed(client_version="0.2.0")

        result = await service.get_session_summary()
        assert result.auth_state == "revoked"  # Hard-deny, not grace

    @pytest.mark.asyncio
    async def test_full_lifecycle_startup_restore_expired(self, auth_db_session, tmp_path):
        """E2E: Startup restore with expired session."""
        now = datetime.now(UTC).replace(tzinfo=None)
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # Setup expired session
        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            expires_at=now - timedelta(minutes=5),  # Expired
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            now_fn=lambda: now,
        )

        result = await service.restore_session()
        assert result.auth_state == "refresh_required"

    @pytest.mark.asyncio
    async def test_full_lifecycle_device_identity_preserved(self, auth_db_session, tmp_path):
        """E2E: Device identity preserved across lifecycle."""
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # First login creates device identity
        login_payload = _session_payload(device_id="device-abc")
        client = DummyRemoteAuthClient(login_result=login_payload)
        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: client,
        )

        await service.login(
            username="alice",
            password="secret",
            device_id="device-abc",
            client_version="0.2.0",
        )

        # Device ID should be persisted
        persisted_device_id = device_store.get_device_id()
        assert persisted_device_id == "device-abc"

        # Logout should preserve device identity
        await service.logout()
        assert device_store.get_device_id() == "device-abc"

    @pytest.mark.asyncio
    async def test_step4_proof_summary(self, auth_db_session, tmp_path):
        """Summary test proving all Step 4 semantics in one flow."""
        now = datetime.now(UTC).replace(tzinfo=None)
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # 1. Login establishes session
        login_payload = _session_payload(
            access_token="token-1",
            refresh_token="refresh-1",
            expires_at=now + timedelta(minutes=3),
            device_id="device-proof",
        )
        client = DummyRemoteAuthClient(login_result=login_payload)
        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: client,
            now_fn=lambda: now,
        )

        result = await service.login(
            username="alice",
            password="secret",
            device_id="device-proof",
            client_version="0.2.0",
        )
        assert result.auth_state == "authenticated_active"

        # 2. Device identity persisted
        assert device_store.get_device_id() == "device-proof"

        # 3. Token rotation on refresh
        refresh_payload = _session_payload(
            access_token="token-2",
            refresh_token="refresh-2",
            expires_at=now + timedelta(hours=1),
            device_id="device-proof",
        )
        client = DummyRemoteAuthClient(refresh_result=refresh_payload)
        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: client,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")
        assert result.auth_state == "authenticated_active"
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) == "token-2"

        # 4. Hard-deny propagation via /me (since refresh already succeeded)
        client = DummyRemoteAuthClient(
            me_exc=RemoteAuthResponseError(
                error_code="revoked",
                message="Revoked",
                status_code=403,
            )
        )
        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: client,
            now_fn=lambda: now,
        )

        with pytest.raises(RemoteAuthResponseError):
            await service.get_me()

        result = await service.get_session_summary()
        assert result.auth_state == "revoked"

        # 5. Logout cleanup
        await service.logout()
        result = await service.get_session_summary()
        assert result.auth_state == "unauthenticated"
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) is None
        assert device_store.get_device_id() == "device-proof"  # Preserved
