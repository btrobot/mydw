"""
Step 1 / PR4 tests for AuthService and local machine-session lifecycle.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.auth_events import AuthEventType, auth_event_emitter
from core.device_identity import FileDeviceIdentityStore
from core.remote_auth_client import RemoteAuthResponseError, RemoteAuthTransportError
from core.secret_store import FileSecretStore
from models import Base, RemoteAuthSession
from schemas.auth import RemoteAuthMePayload, RemoteAuthSessionPayload, RemoteAuthUser
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


def _build_service(
    db: AsyncSession,
    tmp_path: Path,
    *,
    client: DummyRemoteAuthClient,
    now: datetime,
) -> AuthService:
    store = FileSecretStore(path=tmp_path / "secrets.json")
    device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")
    return AuthService(
        db,
        secret_store=store,
        device_identity_store=device_store,
        remote_client_factory=lambda: client,
        now_fn=lambda: now,
    )


@pytest.mark.asyncio
async def test_auth_service_login_persists_active_session_and_secrets(auth_db_session: AsyncSession, tmp_path: Path) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    client = DummyRemoteAuthClient(login_result=_session_payload())
    service = _build_service(auth_db_session, tmp_path, client=client, now=now)

    summary = await service.login(
        username="alice",
        password="secret",
        device_id="device-1",
        client_version="0.2.0",
    )

    assert summary.auth_state == "authenticated_active"
    assert summary.remote_user_id == "u_123"
    assert service.secret_store.get_secret(ACCESS_TOKEN_KEY) == "access-token"
    assert service.secret_store.get_secret(REFRESH_TOKEN_KEY) == "refresh-token"


@pytest.mark.asyncio
async def test_restore_session_marks_refresh_required_when_expired(auth_db_session: AsyncSession, tmp_path: Path) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    session = RemoteAuthSession(
        auth_state="authenticated_active",
        remote_user_id="u_123",
        expires_at=now - timedelta(minutes=1),
        offline_grace_until=now + timedelta(hours=1),
        device_id="device-1",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    service = _build_service(auth_db_session, tmp_path, client=DummyRemoteAuthClient(), now=now)
    # PR2: Must set refresh token for expired session to transition to refresh_required
    service.secret_store.set_secret(REFRESH_TOKEN_KEY, "existing-refresh")
    summary = await service.restore_session()

    assert summary.auth_state == "refresh_required"


@pytest.mark.asyncio
async def test_refresh_success_updates_session_and_rotates_secrets(auth_db_session: AsyncSession, tmp_path: Path) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    session = RemoteAuthSession(
        auth_state="refresh_required",
        remote_user_id="u_123",
        expires_at=now - timedelta(minutes=1),
        offline_grace_until=now + timedelta(hours=1),
        device_id="device-1",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    client = DummyRemoteAuthClient(
        refresh_result=_session_payload(
            access_token="new-access",
            refresh_token="new-refresh",
            expires_at=now + timedelta(hours=1),
            offline_grace_until=now + timedelta(hours=24),
        )
    )
    service = _build_service(auth_db_session, tmp_path, client=client, now=now)
    service.secret_store.set_secret(REFRESH_TOKEN_KEY, "old-refresh")

    summary = await service.refresh_if_needed(client_version="0.2.0")

    assert summary.auth_state == "authenticated_active"
    assert service.secret_store.get_secret(ACCESS_TOKEN_KEY) == "new-access"
    assert service.secret_store.get_secret(REFRESH_TOKEN_KEY) == "new-refresh"


@pytest.mark.asyncio
async def test_refresh_network_failure_enters_grace_when_valid(auth_db_session: AsyncSession, tmp_path: Path) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    session = RemoteAuthSession(
        auth_state="refresh_required",
        remote_user_id="u_123",
        expires_at=now - timedelta(minutes=1),
        offline_grace_until=now + timedelta(hours=2),
        device_id="device-1",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    client = DummyRemoteAuthClient(
        refresh_exc=RemoteAuthTransportError("timeout"),
    )
    service = _build_service(auth_db_session, tmp_path, client=client, now=now)
    service.secret_store.set_secret(REFRESH_TOKEN_KEY, "refresh-token")

    summary = await service.refresh_if_needed(client_version="0.2.0")

    assert summary.auth_state == "authenticated_grace"
    assert summary.denial_reason == "network_timeout"


@pytest.mark.asyncio
async def test_refresh_revoked_sets_revoked_state(auth_db_session: AsyncSession, tmp_path: Path) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    session = RemoteAuthSession(
        auth_state="refresh_required",
        remote_user_id="u_123",
        expires_at=now - timedelta(minutes=1),
        offline_grace_until=now + timedelta(hours=2),
        device_id="device-1",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    client = DummyRemoteAuthClient(
        refresh_exc=RemoteAuthResponseError(
            "revoked",
            "revoked",
            status_code=403,
        )
    )
    service = _build_service(auth_db_session, tmp_path, client=client, now=now)
    service.secret_store.set_secret(REFRESH_TOKEN_KEY, "refresh-token")

    with pytest.raises(RemoteAuthResponseError):
        await service.refresh_if_needed(client_version="0.2.0")

    refreshed = await auth_db_session.get(RemoteAuthSession, session.id)
    assert refreshed.auth_state == "revoked"
    assert refreshed.denial_reason == "revoked"


@pytest.mark.asyncio
async def test_logout_clears_secrets_and_marks_unauthenticated(auth_db_session: AsyncSession, tmp_path: Path) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    session = RemoteAuthSession(
        auth_state="authenticated_active",
        remote_user_id="u_123",
        display_name="Alice",
        license_status="active",
        entitlements_snapshot='["dashboard:view"]',
        expires_at=now + timedelta(hours=1),
        last_verified_at=now,
        offline_grace_until=now + timedelta(hours=24),
        device_id="device-1",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    service = _build_service(auth_db_session, tmp_path, client=DummyRemoteAuthClient(), now=now)
    service.secret_store.set_secret(ACCESS_TOKEN_KEY, "access-token")
    service.secret_store.set_secret(REFRESH_TOKEN_KEY, "refresh-token")

    summary = await service.logout()

    assert summary.auth_state == "unauthenticated"
    assert service.secret_store.get_secret(ACCESS_TOKEN_KEY) is None
    assert service.secret_store.get_secret(REFRESH_TOKEN_KEY) is None


@pytest.mark.asyncio
async def test_get_me_updates_last_verified_and_non_secret_fields(auth_db_session: AsyncSession, tmp_path: Path) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    session = RemoteAuthSession(
        auth_state="authenticated_active",
        remote_user_id="u_123",
        device_id="device-1",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    me_payload = RemoteAuthMePayload(
        user=RemoteAuthUser(
            id="u_123",
            username="alice",
            display_name="Alice Updated",
            tenant_id="tenant_1",
        ),
        license_status="active",
        entitlements=["dashboard:view", "publish:run"],
        device_id="device-1",
        device_status="bound",
        offline_grace_until=now + timedelta(hours=12),
        minimum_supported_version="0.2.0",
    )
    client = DummyRemoteAuthClient(me_result=me_payload)
    service = _build_service(auth_db_session, tmp_path, client=client, now=now)
    service.secret_store.set_secret(ACCESS_TOKEN_KEY, "access-token")

    result = await service.get_me()

    assert result.user.display_name == "Alice Updated"
    refreshed = await auth_db_session.get(RemoteAuthSession, session.id)
    assert refreshed.display_name == "Alice Updated"
    assert refreshed.last_verified_at == now


@pytest.mark.asyncio
async def test_get_session_summary_returns_persisted_machine_session(
    auth_db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    session = RemoteAuthSession(
        auth_state="authenticated_grace",
        remote_user_id="u_123",
        display_name="Alice",
        license_status="active",
        entitlements_snapshot='["dashboard:view"]',
        offline_grace_until=now + timedelta(hours=2),
        denial_reason="network_timeout",
        device_id="device-1",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    service = _build_service(auth_db_session, tmp_path, client=DummyRemoteAuthClient(), now=now)

    summary = await service.get_session_summary()

    assert summary.auth_state == "authenticated_grace"
    assert summary.denial_reason == "network_timeout"
    assert summary.device_id == "device-1"


@pytest.mark.asyncio
async def test_login_disabled_emits_failed_and_revoked_events(auth_db_session: AsyncSession, tmp_path: Path) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    client = DummyRemoteAuthClient(
        login_exc=RemoteAuthResponseError(
            error_code="disabled",
            message="Account disabled",
            status_code=403,
        )
    )
    service = _build_service(auth_db_session, tmp_path, client=client, now=now)

    auth_event_emitter.start_capture()
    with pytest.raises(RemoteAuthResponseError):
        await service.login(
            username="alice",
            password="secret",
            device_id="device-1",
            client_version="0.2.0",
        )
    events = auth_event_emitter.stop_capture()

    assert [event.event_name for event in events] == [
        AuthEventType.AUTH_LOGIN_FAILED,
        AuthEventType.AUTH_REVOKED,
    ]
    assert events[0].auth_state == "revoked"
    assert events[1].reason_code == "disabled"
    assert events[1].extra["previous_state"] == "authorizing"


@pytest.mark.asyncio
async def test_refresh_revoked_emits_previous_state_in_hard_deny_event(
    auth_db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    session = RemoteAuthSession(
        auth_state="refresh_required",
        remote_user_id="u_123",
        expires_at=now - timedelta(minutes=1),
        device_id="device-1",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    client = DummyRemoteAuthClient(
        refresh_exc=RemoteAuthResponseError(
            "revoked",
            "revoked",
            status_code=403,
        )
    )
    service = _build_service(auth_db_session, tmp_path, client=client, now=now)
    service.secret_store.set_secret(REFRESH_TOKEN_KEY, "refresh-token")

    auth_event_emitter.start_capture()
    with pytest.raises(RemoteAuthResponseError):
        await service.refresh_if_needed(client_version="0.2.0")
    events = auth_event_emitter.stop_capture()

    assert [event.event_name for event in events] == [
        AuthEventType.AUTH_REFRESH_STARTED,
        AuthEventType.AUTH_REFRESH_FAILED,
        AuthEventType.AUTH_REVOKED,
    ]
    assert events[1].auth_state == "revoked"
    assert events[2].extra["previous_state"] == "refresh_required"


@pytest.mark.asyncio
async def test_get_me_device_mismatch_emits_hard_deny_followup_event(
    auth_db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    now = datetime(2026, 4, 14, 0, 0, 0)
    session = RemoteAuthSession(
        auth_state="authenticated_active",
        remote_user_id="u_123",
        device_id="device-1",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    client = DummyRemoteAuthClient(
        me_exc=RemoteAuthResponseError(
            error_code="device_mismatch",
            message="Device mismatch",
            status_code=403,
        )
    )
    service = _build_service(auth_db_session, tmp_path, client=client, now=now)
    service.secret_store.set_secret(ACCESS_TOKEN_KEY, "access-token")

    auth_event_emitter.start_capture()
    with pytest.raises(RemoteAuthResponseError):
        await service.get_me()
    events = auth_event_emitter.stop_capture()

    assert [event.event_name for event in events] == [
        AuthEventType.AUTH_ME_VALIDATION_FAILED,
        AuthEventType.AUTH_DEVICE_MISMATCH,
    ]
    assert events[0].auth_state == "device_mismatch"
    assert events[1].extra["previous_state"] == "authenticated_active"
