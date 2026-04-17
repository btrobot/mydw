"""
Pytest configuration and shared fixtures for backend tests.

Provides:
- In-memory SQLite database for test isolation
- FastAPI TestClient via httpx
- Mock browser manager and DewuClient
"""
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend root is on sys.path
backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from core.auth_dependencies import (
    set_current_auth_summary,
    get_machine_session_summary,
    require_active_machine_session,
    require_grace_readonly_machine_session,
)
from core.device_identity import FileDeviceIdentityStore
from core.secret_store import FileSecretStore
import models
from models import Base, Account, RemoteAuthSession, get_db
from main import app
from schemas.auth import LocalAuthSessionSummary


# ============ Database Fixtures ============

@pytest_asyncio.fixture()
async def engine():
    """Create an in-memory SQLite engine for each test."""
    _engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest.fixture(autouse=True)
def isolated_auth_runtime_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Keep AuthService tests hermetic by isolating default file-backed auth artifacts."""
    set_current_auth_summary(None)

    secret_store = FileSecretStore(path=tmp_path / "remote_auth_secrets.json")
    device_store = FileDeviceIdentityStore(path=tmp_path / "remote_auth_device.json")

    monkeypatch.setattr("services.auth_service.create_secret_store", lambda: secret_store)
    monkeypatch.setattr("services.auth_service.create_device_identity_store", lambda: device_store)

    yield

    set_current_auth_summary(None)


@pytest_asyncio.fixture()
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session bound to the test engine."""
    _session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with _session_factory() as session:
        yield session


@pytest_asyncio.fixture()
async def active_remote_auth_session(db_session: AsyncSession) -> RemoteAuthSession:
    session = RemoteAuthSession(
        auth_state="authenticated_active",
        remote_user_id="test-user",
        display_name="Test User",
        license_status="active",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        offline_grace_until=datetime.now(UTC) + timedelta(hours=2),
        device_id="test-device",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest_asyncio.fixture()
async def client(engine) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an httpx AsyncClient with the FastAPI app,
    using the test database engine instead of the real one.
    """
    _session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with _session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    def _active_session_override() -> LocalAuthSessionSummary:
        summary = LocalAuthSessionSummary(
            auth_state="authenticated_active",
            remote_user_id="test-user",
            display_name="Test User",
            license_status="active",
            entitlements=["dashboard:view"],
            device_id="test-device",
        )
        set_current_auth_summary(summary)
        return summary

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_active_machine_session] = _active_session_override
    app.dependency_overrides[require_grace_readonly_machine_session] = _active_session_override
    app.dependency_overrides[get_machine_session_summary] = _active_session_override

    async with _session_factory() as seeded_session:
        seeded_session.add(
            RemoteAuthSession(
                auth_state="authenticated_active",
                remote_user_id="test-user",
                display_name="Test User",
                license_status="active",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                offline_grace_until=datetime.now(UTC) + timedelta(hours=2),
                device_id="test-device",
            )
        )
        await seeded_session.commit()

    original_async_session = models.async_session
    models.async_session = _session_factory

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    models.async_session = original_async_session
    app.dependency_overrides.clear()


# ============ Account Fixtures ============

@pytest_asyncio.fixture()
async def sample_account(client: AsyncClient) -> dict:
    """Create a sample account and return the response dict."""
    response = await client.post(
        "/api/accounts/",
        json={"account_id": "test_user_001", "account_name": "Test Account"},
    )
    assert response.status_code == 201
    return response.json()


# ============ Mock Fixtures ============

@pytest.fixture()
def mock_browser_manager():
    """
    Mock the global browser_manager to prevent real Patchright usage in tests.
    """
    mock = MagicMock()
    mock.init = AsyncMock()
    mock.close = AsyncMock()
    mock.new_page = AsyncMock(return_value=MagicMock())
    mock.create_context = AsyncMock(return_value=MagicMock())
    mock.get_context = AsyncMock(return_value=None)
    mock.get_or_create_context = AsyncMock(return_value=MagicMock())
    mock.close_context = AsyncMock()
    mock.save_storage_state = AsyncMock(return_value="encrypted_state_data")
    return mock


@pytest.fixture()
def mock_dewu_client():
    """
    Mock DewuClient for testing connection flow without real browser.
    """
    mock = MagicMock()
    mock.login_with_sms = AsyncMock(return_value=(True, "Login successful"))
    mock.save_login_session = AsyncMock(return_value="encrypted_storage_state")
    mock.page = MagicMock()
    return mock
