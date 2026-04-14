"""
Step 5 PR5: auth admin API tests.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

backend_root = str(Path(__file__).parent.parent)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import api.auth as auth_api
from core.auth_dependencies import require_active_machine_session
from core.device_identity import FileDeviceIdentityStore
from core.secret_store import FileSecretStore
from models import RemoteAuthSession
from schemas.auth import LocalAuthSessionSummary
from services.auth_service import ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, AuthService
from main import app


@pytest.fixture()
def restore_auth_admin_state():
    original = auth_api.build_auth_service
    original_active = app.dependency_overrides.get(require_active_machine_session)
    original_admin = app.dependency_overrides.get(auth_api.require_auth_admin)
    yield
    auth_api.build_auth_service = original
    if original_active is None:
        app.dependency_overrides.pop(require_active_machine_session, None)
    else:
        app.dependency_overrides[require_active_machine_session] = original_active
    if original_admin is None:
        app.dependency_overrides.pop(auth_api.require_auth_admin, None)
    else:
        app.dependency_overrides[auth_api.require_auth_admin] = original_admin


class TestAuthAdminAPI:
    @pytest.fixture(autouse=True)
    def allow_admin(self):
        app.dependency_overrides[auth_api.require_auth_admin] = lambda: LocalAuthSessionSummary(
            auth_state="authenticated_active",
            remote_user_id="admin-user",
            display_name="Admin",
            entitlements=["dashboard:view", "auth:admin"],
            device_id="device-1",
        )
        yield

    @pytest.mark.asyncio
    async def test_admin_sessions_list(
        self,
        client: AsyncClient,
        engine,
        tmp_path: Path,
        restore_auth_admin_state,
    ) -> None:
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            await session.execute(delete(RemoteAuthSession))
            session.add(
                RemoteAuthSession(
                    auth_state="authenticated_active",
                    remote_user_id="u_123",
                    display_name="Alice",
                    license_status="active",
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                    offline_grace_until=datetime.now(UTC) + timedelta(hours=2),
                    device_id="device-1",
                )
            )
            await session.commit()

        secret_store = FileSecretStore(path=tmp_path / "admin-secrets.json")
        secret_store.set_secret(ACCESS_TOKEN_KEY, "access-token")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "refresh-token")
        device_store = FileDeviceIdentityStore(path=tmp_path / "admin-device.json")
        device_store.set_device_id("device-1")

        auth_api.build_auth_service = lambda db: AuthService(
            db,
            secret_store=secret_store,
            device_identity_store=device_store,
        )

        response = await client.get("/api/admin/sessions")

        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["remote_user_id"] == "u_123"
        assert payload[0]["is_current_session"] is True
        assert payload[0]["has_access_token"] is True

    @pytest.mark.asyncio
    async def test_admin_session_revoke(
        self,
        client: AsyncClient,
        engine,
        tmp_path: Path,
        restore_auth_admin_state,
    ) -> None:
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            await session.execute(delete(RemoteAuthSession))
            current = RemoteAuthSession(
                auth_state="authenticated_active",
                remote_user_id="u_123",
                display_name="Alice",
                license_status="active",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                offline_grace_until=datetime.now(UTC) + timedelta(hours=2),
                device_id="device-1",
            )
            session.add(current)
            await session.commit()
            await session.refresh(current)
            session_id = current.id

        secret_store = FileSecretStore(path=tmp_path / "revoke-secrets.json")
        secret_store.set_secret(ACCESS_TOKEN_KEY, "access-token")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "refresh-token")
        device_store = FileDeviceIdentityStore(path=tmp_path / "revoke-device.json")
        device_store.set_device_id("device-1")

        auth_api.build_auth_service = lambda db: AuthService(
            db,
            secret_store=secret_store,
            device_identity_store=device_store,
        )

        response = await client.post(f"/api/admin/sessions/{session_id}/revoke")

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["revoked_session"]["auth_state"] == "revoked"
        assert payload["revoked_session"]["denial_reason"] == "admin_revoked"
        assert payload["current_session"]["auth_state"] == "revoked"
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) is None
        assert secret_store.get_secret(REFRESH_TOKEN_KEY) is None

    @pytest.mark.asyncio
    async def test_admin_revoke_historical_session_preserves_current_session(
        self,
        client: AsyncClient,
        engine,
        tmp_path: Path,
        restore_auth_admin_state,
    ) -> None:
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_factory() as session:
            await session.execute(delete(RemoteAuthSession))
            historical = RemoteAuthSession(
                auth_state="authenticated_active",
                remote_user_id="u_old",
                display_name="Old Session",
                license_status="active",
                device_id="device-old",
            )
            current = RemoteAuthSession(
                auth_state="authenticated_active",
                remote_user_id="u_current",
                display_name="Current Session",
                license_status="active",
                device_id="device-current",
            )
            session.add_all([historical, current])
            await session.commit()
            await session.refresh(historical)
            historical_session_id = historical.id

        secret_store = FileSecretStore(path=tmp_path / "historical-secrets.json")
        secret_store.set_secret(ACCESS_TOKEN_KEY, "access-token")
        secret_store.set_secret(REFRESH_TOKEN_KEY, "refresh-token")
        device_store = FileDeviceIdentityStore(path=tmp_path / "historical-device.json")
        device_store.set_device_id("device-current")

        auth_api.build_auth_service = lambda db: AuthService(
            db,
            secret_store=secret_store,
            device_identity_store=device_store,
        )

        response = await client.post(f"/api/admin/sessions/{historical_session_id}/revoke")

        assert response.status_code == 200
        payload = response.json()
        assert payload["revoked_session"]["session_id"] == historical_session_id
        assert payload["revoked_session"]["is_current_session"] is False
        assert payload["current_session"]["remote_user_id"] == "u_current"
        assert payload["current_session"]["auth_state"] == "authenticated_active"
        assert secret_store.get_secret(ACCESS_TOKEN_KEY) == "access-token"
        assert secret_store.get_secret(REFRESH_TOKEN_KEY) == "refresh-token"

    @pytest.mark.asyncio
    async def test_admin_unauthorized_for_non_admin(
        self,
        client: AsyncClient,
        restore_auth_admin_state,
    ) -> None:
        app.dependency_overrides[auth_api.require_auth_admin] = lambda: (_ for _ in ()).throw(
            HTTPException(
                status_code=403,
                detail={
                    "error_code": "forbidden",
                    "message": "Admin privileges required.",
                },
            )
        )

        response = await client.get("/api/admin/sessions")

        assert response.status_code == 403
        assert response.json()["detail"]["error_code"] == "forbidden"
