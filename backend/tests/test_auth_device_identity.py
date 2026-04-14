"""
Step 4 / PR1 tests for local device identity foundation.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.device_identity import FileDeviceIdentityStore
from core.secret_store import FileSecretStore
from models import Base, RemoteAuthSession
from schemas.auth import RemoteAuthMePayload, RemoteAuthSessionPayload, RemoteAuthUser
from services.auth_service import AuthService


class DummyRemoteAuthClient:
    def __init__(self, *, login_result=None, refresh_result=None, me_result=None) -> None:
        self.login_result = login_result
        self.refresh_result = refresh_result
        self.me_result = me_result
        self.login_calls: list[dict] = []
        self.refresh_calls: list[dict] = []
        self.me_calls: list[dict] = []

    async def login(self, **kwargs):
        self.login_calls.append(kwargs)
        return self.login_result

    async def refresh(self, **kwargs):
        self.refresh_calls.append(kwargs)
        return self.refresh_result

    async def me(self, **kwargs):
        self.me_calls.append(kwargs)
        return self.me_result

    async def aclose(self) -> None:
        return None


def _session_payload(
    *,
    device_id: str,
    access_token: str = "access-token",
    refresh_token: str = "refresh-token",
) -> RemoteAuthSessionPayload:
    return RemoteAuthSessionPayload(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime(2026, 4, 20, 10, 0, 0),
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
        offline_grace_until=datetime(2026, 4, 21, 10, 0, 0),
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
) -> AuthService:
    secret_store = FileSecretStore(path=tmp_path / "secrets.json")
    device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")
    return AuthService(
        db,
        secret_store=secret_store,
        device_identity_store=device_store,
        remote_client_factory=lambda: client,
        now_fn=lambda: datetime.now(UTC).replace(tzinfo=None),
    )


def test_file_device_identity_store_persists_seeded_device_id(tmp_path: Path) -> None:
    store = FileDeviceIdentityStore(path=tmp_path / "device.json")

    created = store.get_or_create("frontend-seed")
    reloaded = FileDeviceIdentityStore(path=tmp_path / "device.json")

    assert created == "frontend-seed"
    assert reloaded.get_device_id() == "frontend-seed"


def test_file_device_identity_store_generates_stable_id_once_created(tmp_path: Path) -> None:
    store = FileDeviceIdentityStore(path=tmp_path / "device.json")

    generated = store.get_or_create()
    reused = store.get_or_create("ignored-seed")

    assert generated.startswith("device-")
    assert generated == reused


@pytest.mark.asyncio
async def test_auth_service_login_uses_persisted_device_id_after_first_seed(
    auth_db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    client = DummyRemoteAuthClient(login_result=_session_payload(device_id="frontend-seed"))
    service = _build_service(auth_db_session, tmp_path, client=client)

    first = await service.login(
        username="alice",
        password="secret",
        device_id="frontend-seed",
        client_version="0.2.0",
    )
    second = await service.login(
        username="alice",
        password="secret",
        device_id="other-seed",
        client_version="0.2.0",
    )

    assert first.device_id == "frontend-seed"
    assert second.device_id == "frontend-seed"
    assert client.login_calls[0]["device_id"] == "frontend-seed"
    assert client.login_calls[1]["device_id"] == "frontend-seed"


@pytest.mark.asyncio
async def test_refresh_uses_canonical_persisted_device_id(
    auth_db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    session = RemoteAuthSession(
        auth_state="refresh_required",
        remote_user_id="u_123",
        expires_at=datetime(2026, 4, 14, 0, 0, 0),
        device_id=None,
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    client = DummyRemoteAuthClient(
        refresh_result=_session_payload(device_id="stored-device", access_token="new-access", refresh_token="new-refresh")
    )
    service = _build_service(auth_db_session, tmp_path, client=client)
    service.device_identity_store.set_device_id("stored-device")
    service.secret_store.set_secret("remote_auth.refresh_token", "refresh-token")

    summary = await service.refresh_if_needed(client_version="0.2.0")

    assert summary.device_id == "stored-device"
    assert client.refresh_calls[0]["device_id"] == "stored-device"


@pytest.mark.asyncio
async def test_get_me_syncs_device_identity_store_from_remote_payload(
    auth_db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    session = RemoteAuthSession(
        auth_state="authenticated_active",
        remote_user_id="u_123",
        device_id="old-device",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    me_payload = RemoteAuthMePayload(
        user=RemoteAuthUser(
            id="u_123",
            username="alice",
            display_name="Alice",
            tenant_id="tenant_1",
        ),
        license_status="active",
        entitlements=["dashboard:view"],
        device_id="remote-device",
        device_status="bound",
        offline_grace_until=datetime(2026, 4, 21, 10, 0, 0),
        minimum_supported_version="0.2.0",
    )
    client = DummyRemoteAuthClient(me_result=me_payload)
    service = _build_service(auth_db_session, tmp_path, client=client)
    service.secret_store.set_secret("remote_auth.access_token", "access-token")

    await service.get_me()

    assert service.device_identity_store.get_device_id() == "remote-device"


@pytest.mark.asyncio
async def test_logout_keeps_local_device_identity_foundation(
    auth_db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    session = RemoteAuthSession(
        auth_state="authenticated_active",
        remote_user_id="u_123",
        device_id="persisted-device",
    )
    auth_db_session.add(session)
    await auth_db_session.commit()

    client = DummyRemoteAuthClient()
    service = _build_service(auth_db_session, tmp_path, client=client)
    service.device_identity_store.set_device_id("persisted-device")
    service.secret_store.set_secret("remote_auth.access_token", "access-token")
    service.secret_store.set_secret("remote_auth.refresh_token", "refresh-token")

    summary = await service.logout()

    assert summary.auth_state == "unauthenticated"
    assert summary.device_id == "persisted-device"
    assert service.device_identity_store.get_device_id() == "persisted-device"
