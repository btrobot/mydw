"""
Pytest configuration and shared fixtures for backend tests.

Provides:
- In-memory SQLite database for test isolation
- FastAPI TestClient via httpx
- Mock browser manager and DewuClient
"""
import sys
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

from models import Base, Account, get_db
from main import app


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


@pytest_asyncio.fixture()
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session bound to the test engine."""
    _session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with _session_factory() as session:
        yield session


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

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

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
