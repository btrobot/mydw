"""
Step 5 PR3: auth status API tests.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import api.auth as auth_api
from core.device_identity import FileDeviceIdentityStore
from core.secret_store import FileSecretStore
from models import RemoteAuthSession
from schemas.auth import AuthHealthResponse, AuthStatusResponse, SessionDetailsResponse
from services.auth_service import AuthService


class DummyStatusAuthService:
    async def get_status(self):
        return {
            "auth_state": "authenticated_grace",
            "remote_user_id": "u_123",
            "display_name": "Alice",
            "license_status": "active",
            "device_id": "device-1",
            "denial_reason": "network_timeout",
            "expires_at": "2026-04-20T11:00:00",
            "last_verified_at": "2026-04-14T00:10:00",
            "offline_grace_until": "2026-04-21T10:00:00",
            "token_expires_in_seconds": 123,
            "grace_remaining_seconds": 456,
            "is_authenticated": True,
            "is_active": False,
            "is_grace": True,
            "requires_reauth": False,
            "can_read_local_data": True,
            "can_run_protected_actions": False,
            "can_run_background_tasks": False,
        }

    async def get_health(self):
        return {
            "status": "degraded",
            "auth_state": "authenticated_grace",
            "denial_reason": "network_timeout",
            "has_access_token": True,
            "has_refresh_token": True,
            "token_expires_in_seconds": 123,
            "grace_remaining_seconds": 456,
            "last_verified_at": "2026-04-14T00:10:00",
            "can_read_local_data": True,
            "can_run_protected_actions": False,
            "can_run_background_tasks": False,
        }

    async def get_session_details(self):
        return {
            "session_id": 1,
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
            "has_access_token": True,
            "has_refresh_token": True,
            "created_at": "2026-04-14T00:00:00",
            "updated_at": "2026-04-14T00:10:00",
        }


@pytest.fixture()
def restore_auth_service_builder():
    original = auth_api.build_auth_service
    yield
    auth_api.build_auth_service = original


def test_status_response_format() -> None:
    payload = AuthStatusResponse(
        auth_state="authenticated_active",
        is_authenticated=True,
        is_active=True,
        is_grace=False,
        requires_reauth=False,
        can_read_local_data=True,
        can_run_protected_actions=True,
        can_run_background_tasks=True,
    )
    assert payload.auth_state == "authenticated_active"
    assert payload.is_authenticated is True


def test_health_response_format() -> None:
    payload = AuthHealthResponse(
        status="healthy",
        auth_state="authenticated_active",
        has_access_token=True,
        has_refresh_token=True,
        can_read_local_data=True,
        can_run_protected_actions=True,
        can_run_background_tasks=True,
    )
    assert payload.status == "healthy"
    assert payload.has_access_token is True


def test_details_response_format() -> None:
    payload = SessionDetailsResponse(auth_state="unauthenticated")
    assert payload.auth_state == "unauthenticated"
    assert payload.has_access_token is False


class TestAuthStatusAPI:
    @pytest.mark.asyncio
    async def test_status_endpoint_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/status")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_status_unauthenticated(self, client: AsyncClient, restore_auth_service_builder) -> None:
        class UnauthStatusService(DummyStatusAuthService):
            async def get_status(self):
                return {
                    "auth_state": "unauthenticated",
                    "remote_user_id": None,
                    "display_name": None,
                    "license_status": None,
                    "device_id": None,
                    "denial_reason": None,
                    "expires_at": None,
                    "last_verified_at": None,
                    "offline_grace_until": None,
                    "token_expires_in_seconds": None,
                    "grace_remaining_seconds": None,
                    "is_authenticated": False,
                    "is_active": False,
                    "is_grace": False,
                    "requires_reauth": True,
                    "can_read_local_data": False,
                    "can_run_protected_actions": False,
                    "can_run_background_tasks": False,
                }

        auth_api.build_auth_service = lambda db: UnauthStatusService()
        response = await client.get("/api/auth/status")
        assert response.status_code == 200
        assert response.json()["auth_state"] == "unauthenticated"
        assert response.json()["requires_reauth"] is True

    @pytest.mark.asyncio
    async def test_status_authenticated_active(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_state"] == "authenticated_active"
        assert payload["is_active"] is True
        assert payload["can_run_background_tasks"] is True

    @pytest.mark.asyncio
    async def test_status_authenticated_grace(self, client: AsyncClient, restore_auth_service_builder) -> None:
        auth_api.build_auth_service = lambda db: DummyStatusAuthService()
        response = await client.get("/api/auth/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_state"] == "authenticated_grace"
        assert payload["is_grace"] is True
        assert payload["can_run_protected_actions"] is False

    @pytest.mark.asyncio
    async def test_status_revoked(self, client: AsyncClient, restore_auth_service_builder) -> None:
        class RevokedStatusService(DummyStatusAuthService):
            async def get_status(self):
                return {
                    "auth_state": "revoked",
                    "remote_user_id": "u_123",
                    "display_name": "Alice",
                    "license_status": "active",
                    "device_id": "device-1",
                    "denial_reason": "revoked",
                    "expires_at": None,
                    "last_verified_at": "2026-04-14T00:10:00",
                    "offline_grace_until": None,
                    "token_expires_in_seconds": None,
                    "grace_remaining_seconds": None,
                    "is_authenticated": False,
                    "is_active": False,
                    "is_grace": False,
                    "requires_reauth": True,
                    "can_read_local_data": False,
                    "can_run_protected_actions": False,
                    "can_run_background_tasks": False,
                }

        auth_api.build_auth_service = lambda db: RevokedStatusService()
        response = await client.get("/api/auth/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_state"] == "revoked"
        assert payload["requires_reauth"] is True

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self, client: AsyncClient, restore_auth_service_builder) -> None:
        auth_api.build_auth_service = lambda db: DummyStatusAuthService()
        response = await client.get("/api/auth/health")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_session_details_endpoint_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/session/details")
        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_state"] == "authenticated_active"
        assert "has_access_token" in payload

    @pytest.mark.asyncio
    async def test_status_real_service_normalizes_expired_active_to_refresh_required(
        self,
        client: AsyncClient,
        engine,
        tmp_path: Path,
        restore_auth_service_builder,
    ) -> None:
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            await session.execute(delete(RemoteAuthSession))
            session.add(
                RemoteAuthSession(
                    auth_state="authenticated_active",
                    remote_user_id="u_123",
                    device_id="device-1",
                    expires_at=datetime(2000, 1, 1, 0, 0, 0),
                )
            )
            await session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")
        auth_api.build_auth_service = lambda db: AuthService(
            db,
            secret_store=secret_store,
            device_identity_store=device_store,
        )

        response = await client.get("/api/auth/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_state"] == "refresh_required"
        assert payload["requires_reauth"] is False

    @pytest.mark.asyncio
    async def test_status_real_service_normalizes_expired_grace_to_expired(
        self,
        client: AsyncClient,
        engine,
        tmp_path: Path,
        restore_auth_service_builder,
    ) -> None:
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            await session.execute(delete(RemoteAuthSession))
            session.add(
                RemoteAuthSession(
                    auth_state="authenticated_grace",
                    remote_user_id="u_123",
                    device_id="device-1",
                    offline_grace_until=datetime(2000, 1, 1, 0, 0, 0),
                    denial_reason="network_timeout",
                )
            )
            await session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")
        auth_api.build_auth_service = lambda db: AuthService(
            db,
            secret_store=secret_store,
            device_identity_store=device_store,
        )

        response = await client.get("/api/auth/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_state"] == "expired"
        assert payload["requires_reauth"] is True

    @pytest.mark.asyncio
    async def test_status_real_service_detects_device_id_drift(
        self,
        client: AsyncClient,
        engine,
        tmp_path: Path,
        restore_auth_service_builder,
    ) -> None:
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            await session.execute(delete(RemoteAuthSession))
            session.add(
                RemoteAuthSession(
                    auth_state="authenticated_active",
                    remote_user_id="u_123",
                    device_id="server-device",
                )
            )
            await session.commit()

        secret_store = FileSecretStore(path=tmp_path / "secrets.json")
        device_store = FileDeviceIdentityStore(path=tmp_path / "device.json")
        device_store.set_device_id("local-device")
        auth_api.build_auth_service = lambda db: AuthService(
            db,
            secret_store=secret_store,
            device_identity_store=device_store,
        )

        response = await client.get("/api/auth/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["auth_state"] == "device_mismatch"
        assert payload["requires_reauth"] is True
