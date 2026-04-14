"""
Step 4 PR2 tests: Hardened refresh flow, token rotation, and session restore semantics.

PR2 Goals:
- Token rotation success/failure ordering
- Startup restore transitions (authenticated_active -> refresh_required -> active|grace|expired)
- /me validation updates last_verified_at
- Persistence tests for secret rotation and logout cleanup
- Atomic token storage
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.device_identity import FileDeviceIdentityStore
from core.remote_auth_client import RemoteAuthResponseError, RemoteAuthTransportError
from core.secret_store import FileSecretStore
from models import Base, RemoteAuthSession
from schemas.auth import RemoteAuthMePayload, RemoteAuthSessionPayload, RemoteAuthUser
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


def _me_payload(device_id: str = "device-1") -> RemoteAuthMePayload:
    return RemoteAuthMePayload(
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
        offline_grace_until=datetime(2026, 4, 20, 10, 0, 0),
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


class TestTokenRotation:
    """PR2: Token rotation success/failure ordering tests."""

    @pytest.mark.asyncio
    async def test_refresh_success_rotates_tokens_atomically(
        self, auth_db_session, tmp_path
    ):
        """Token rotation must update both access and refresh tokens atomically."""
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # Setup initial tokens
        secret_store.set_secret(ACCESS_TOKEN_KEY, "old-access")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "old-refresh")

        # Create active session nearing expiry
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            expires_at=now + timedelta(minutes=1),  # Within proactive buffer
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        # Mock refresh returning new tokens
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

        # Assert success
        assert result.auth_state == "authenticated_active"

        # Assert both tokens rotated
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) == "new-access"
        assert secret_store.get_secret(REFRESH_TOKEN_KEY) == "new-refresh"

    @pytest.mark.asyncio
    async def test_refresh_failure_preserves_old_tokens(
        self, auth_db_session, tmp_path
    ):
        """Failed refresh must not corrupt stored tokens."""
        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # Setup initial tokens
        secret_store.set_secret(ACCESS_TOKEN_KEY, "existing-access")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "existing-refresh")

        # Create active session
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            expires_at=now - timedelta(minutes=1),  # Expired
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        # Mock refresh failure
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

        # Assert tokens preserved after network failure
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) == "existing-access"
        assert secret_store.get_secret(REFRESH_TOKEN_KEY) == "existing-refresh"


class TestSessionRestore:
    """PR2: Startup restore transition tests."""

    @pytest.mark.asyncio
    async def test_restore_expired_active_to_refresh_required(
        self, auth_db_session, tmp_path
    ):
        """Expired active session transitions to refresh_required."""
        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5),
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
        )

        result = await service.restore_session()

        assert result.auth_state == "refresh_required"

    @pytest.mark.asyncio
    async def test_restore_expired_active_missing_refresh_to_refresh_required(
        self, auth_db_session, tmp_path
    ):
        """Expired active session transitions to refresh_required (refresh_if_needed handles missing token)."""
        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5),
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")
        # No refresh token stored

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
        )

        result = await service.restore_session()

        # PR2: restore_session marks expired active as refresh_required
        # Missing refresh token is handled by refresh_if_needed
        assert result.auth_state == "refresh_required"

    @pytest.mark.asyncio
    async def test_refresh_if_needed_missing_token_to_unauthenticated(
        self, auth_db_session, tmp_path
    ):
        """refresh_if_needed transitions refresh_required without token to unauthenticated."""
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
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")
        # No refresh token stored

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")

        assert result.auth_state == "unauthenticated"
        assert result.denial_reason == "missing_refresh_token"

    @pytest.mark.asyncio
    async def test_restore_grace_expired_to_expired(
        self, auth_db_session, tmp_path
    ):
        """Grace period exceeded transitions to expired."""
        now = datetime.now(UTC).replace(tzinfo=None)
        session = RemoteAuthSession(
            auth_state="authenticated_grace",
            remote_user_id="u_123",
            offline_grace_until=now - timedelta(minutes=5),
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

    @pytest.mark.asyncio
    async def test_restore_valid_grace_unchanged(
        self, auth_db_session, tmp_path
    ):
        """Valid grace period remains unchanged."""
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

        result = await service.restore_session()

        assert result.auth_state == "authenticated_grace"


class TestMeValidation:
    """PR2: /me validation updates session tests."""

    @pytest.mark.asyncio
    async def test_get_me_updates_last_verified_at(
        self, auth_db_session, tmp_path
    ):
        """Successful /me call updates last_verified_at timestamp."""
        now = datetime.now(UTC).replace(tzinfo=None)
        past = now - timedelta(hours=1)

        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            last_verified_at=past,
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(ACCESS_TOKEN_KEY, "valid-access")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        dummy_client = DummyRemoteAuthClient(me_result=_me_payload())

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        result = await service.get_me()

        # Refresh session to get updated last_verified_at
        await auth_db_session.refresh(session)
        assert session.last_verified_at == now

    @pytest.mark.asyncio
    async def test_get_me_remote_rejection_updates_session(
        self, auth_db_session, tmp_path
    ):
        """Remote rejection from /me updates session state."""
        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(ACCESS_TOKEN_KEY, "revoked-access")
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

        # Refresh session to check updated state
        await auth_db_session.refresh(session)
        assert session.auth_state == "revoked"


class TestSecretStoreAtomicity:
    """PR2: Secret store atomic operations tests."""

    def test_set_secrets_atomic(self, tmp_path):
        """set_secrets updates all secrets atomically."""
        store = FileSecretStore(path=tmp_path / "secrets.json")

        store.set_secrets({
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
        })

        assert store.get_secret("key1") == "value1"
        assert store.get_secret("key2") == "value2"
        assert store.get_secret("key3") == "value3"

    def test_set_secrets_overwrites_existing(self, tmp_path):
        """set_secrets overwrites existing keys."""
        store = FileSecretStore(path=tmp_path / "secrets.json")

        store.set_secret("key1", "old-value")
        store.set_secrets({
            "key1": "new-value",
            "key2": "value2",
        })

        assert store.get_secret("key1") == "new-value"
        assert store.get_secret("key2") == "value2"

    def test_logout_clears_secrets(self, tmp_path):
        """Logout clears all stored secrets."""
        store = FileSecretStore(path=tmp_path / "secrets.json")

        store.set_secret(ACCESS_TOKEN_KEY, "access")
        store.set_secret(REFRESH_TOKEN_KEY, "refresh")

        store.clear()

        assert store.get_secret(ACCESS_TOKEN_KEY) is None
        assert store.get_secret(REFRESH_TOKEN_KEY) is None


class TestProactiveRefresh:
    """PR2: Proactive refresh before expiry tests."""

    @pytest.mark.asyncio
    async def test_proactive_refresh_triggered_before_expiry(
        self, auth_db_session, tmp_path
    ):
        """Refresh triggered proactively before token expiry."""
        now = datetime.now(UTC).replace(tzinfo=None)
        # Token expires in 3 minutes (within 5-minute proactive buffer)
        expires_at = now + timedelta(minutes=3)

        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            expires_at=expires_at,
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "valid-refresh")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # Mock successful refresh
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

        # Should have refreshed
        assert result.auth_state == "authenticated_active"
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) == "new-access"

    @pytest.mark.asyncio
    async def test_no_refresh_when_token_valid_and_not_near_expiry(
        self, auth_db_session, tmp_path
    ):
        """No refresh when token is valid and not near expiry."""
        now = datetime.now(UTC).replace(tzinfo=None)
        # Token expires in 30 minutes (outside 5-minute proactive buffer)
        expires_at = now + timedelta(minutes=30)

        session = RemoteAuthSession(
            auth_state="authenticated_active",
            remote_user_id="u_123",
            expires_at=expires_at,
            device_id="device-1",
        )
        auth_db_session.add(session)
        await auth_db_session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        secret_store.set_secret(ACCESS_TOKEN_KEY, "existing-access")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")

        # Mock that should NOT be called
        dummy_client = DummyRemoteAuthClient()
        dummy_client.refresh = AsyncMock()

        service = AuthService(
            auth_db_session,
            secret_store=secret_store,
            device_identity_store=device_store,
            remote_client_factory=lambda: dummy_client,
            now_fn=lambda: now,
        )

        result = await service.refresh_if_needed(client_version="0.2.0")

        # Should not have refreshed
        assert result.auth_state == "authenticated_active"
        dummy_client.refresh.assert_not_called()
