from __future__ import annotations

from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
REMOTE_BACKEND_ROOT = ROOT / "remote" / "remote-backend"
if str(REMOTE_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(REMOTE_BACKEND_ROOT))

from app.api.admin import admin_login_rate_limiter
from app.api.auth import login_rate_limiter, refresh_rate_limiter
from app.core.config import reset_settings_cache
from app.core.db import reset_db_state, session_scope
from app.core.security import hash_password
from app.main import create_app
from app.migrations.runner import downgrade, upgrade
from app.models import AuditLog, License, User, UserCredential, UserEntitlement


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "remote_b0_pr3.sqlite3"
    monkeypatch.setenv("REMOTE_BACKEND_DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    reset_settings_cache()
    reset_db_state()
    login_rate_limiter.reset()
    refresh_rate_limiter.reset()
    admin_login_rate_limiter.reset()
    upgrade()
    yield
    downgrade()
    login_rate_limiter.reset()
    refresh_rate_limiter.reset()
    admin_login_rate_limiter.reset()
    reset_db_state()
    reset_settings_cache()


def get_client() -> TestClient:
    return TestClient(create_app())


def seed_user(*, username: str, password: str, tenant_id: str) -> None:
    with session_scope() as session:
        user = User(username=username, display_name=username.title(), email=f"{username}@example.com", status="active", tenant_id=tenant_id)
        session.add(user)
        session.flush()
        session.add(UserCredential(user_id=user.id, password_hash=hash_password(password)))
        session.add(
            License(
                user_id=user.id,
                license_status="active",
                plan_code="starter",
                starts_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
                offline_grace_hours=24,
            )
        )
        session.add(UserEntitlement(user_id=user.id, entitlement="dashboard:view", source="test"))


def login_as(client: TestClient, *, username: str, password: str, device_id: str) -> dict:
    response = client.post(
        "/login",
        json={
            "username": username,
            "password": password,
            "device_id": device_id,
            "client_version": "0.2.0",
        },
    )
    assert response.status_code == 200, response.json()
    return response.json()


def test_self_revoke_is_idempotent_and_revokes_refresh_token() -> None:
    client = get_client()
    first = login_as(client, username="alice", password="secret", device_id="device_primary")
    second = login_as(client, username="alice", password="secret", device_id="device_primary")

    sessions = client.get("/self/sessions", headers={"Authorization": f"Bearer {second['access_token']}"})
    assert sessions.status_code == 200
    target_session_id = next(item["session_id"] for item in sessions.json()["items"] if not item["is_current"])

    first_revoke = client.post(
        f"/self/sessions/{target_session_id}/revoke",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert first_revoke.status_code == 200
    assert first_revoke.json() == {
        "success": True,
        "session_id": target_session_id,
        "auth_state": "revoked",
        "already_revoked": False,
    }

    revoked_refresh = client.post(
        "/refresh",
        json={
            "refresh_token": first["refresh_token"],
            "device_id": "device_primary",
            "client_version": "0.2.0",
        },
    )
    assert revoked_refresh.status_code == 403
    assert revoked_refresh.json()["error_code"] == "revoked"

    second_revoke = client.post(
        f"/self/sessions/{target_session_id}/revoke",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert second_revoke.status_code == 200
    assert second_revoke.json()["already_revoked"] is True


def test_self_revoke_masks_foreign_and_missing_sessions_with_not_found() -> None:
    seed_user(username="bob", password="hunter2", tenant_id="tenant_2")
    client = get_client()
    alice = login_as(client, username="alice", password="secret", device_id="device_alice")
    bob = login_as(client, username="bob", password="hunter2", device_id="device_bob")

    bob_sessions = client.get("/self/sessions", headers={"Authorization": f"Bearer {bob['access_token']}"})
    assert bob_sessions.status_code == 200
    bob_session_id = bob_sessions.json()["items"][0]["session_id"]

    foreign = client.post(
        f"/self/sessions/{bob_session_id}/revoke",
        headers={"Authorization": f"Bearer {alice['access_token']}"},
    )
    assert foreign.status_code == 404
    assert foreign.json()["error_code"] == "not_found"

    missing = client.post(
        "/self/sessions/sess_missing/revoke",
        headers={"Authorization": f"Bearer {alice['access_token']}"},
    )
    assert missing.status_code == 404
    assert missing.json()["error_code"] == "not_found"

    bob_refresh = client.post(
        "/refresh",
        json={
            "refresh_token": bob["refresh_token"],
            "device_id": "device_bob",
            "client_version": "0.2.0",
        },
    )
    assert bob_refresh.status_code == 200, bob_refresh.json()


def test_self_revoke_writes_frozen_audit_event() -> None:
    client = get_client()
    login_as(client, username="alice", password="secret", device_id="device_audit")
    second = login_as(client, username="alice", password="secret", device_id="device_audit")

    sessions = client.get("/self/sessions", headers={"Authorization": f"Bearer {second['access_token']}"})
    target_session_id = next(item["session_id"] for item in sessions.json()["items"] if not item["is_current"])

    response = client.post(
        f"/self/sessions/{target_session_id}/revoke",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert response.status_code == 200

    with session_scope() as session:
        audit = (
            session.query(AuditLog)
            .filter_by(event_type="self_session_revoked", target_session_id=target_session_id)
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert audit is not None
        assert audit.actor_type == "user"
        assert audit.target_user_id == "1"
        assert audit.details_json is not None
        assert '"already_revoked": false' in audit.details_json


def test_self_revoke_repeat_writes_audit_event_with_already_revoked_true() -> None:
    client = get_client()
    login_as(client, username="alice", password="secret", device_id="device_repeat_audit")
    second = login_as(client, username="alice", password="secret", device_id="device_repeat_audit")

    sessions = client.get("/self/sessions", headers={"Authorization": f"Bearer {second['access_token']}"})
    target_session_id = next(item["session_id"] for item in sessions.json()["items"] if not item["is_current"])

    first_revoke = client.post(
        f"/self/sessions/{target_session_id}/revoke",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert first_revoke.status_code == 200

    repeat_revoke = client.post(
        f"/self/sessions/{target_session_id}/revoke",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert repeat_revoke.status_code == 200
    assert repeat_revoke.json()["already_revoked"] is True

    with session_scope() as session:
        audits = (
            session.query(AuditLog)
            .filter_by(event_type="self_session_revoked", target_session_id=target_session_id)
            .order_by(AuditLog.id.desc())
            .limit(2)
            .all()
        )
        assert len(audits) == 2
        latest_details = json.loads(audits[0].details_json or "{}")
        previous_details = json.loads(audits[1].details_json or "{}")
        assert latest_details["already_revoked"] is True
        assert previous_details["already_revoked"] is False


def test_self_revoke_requires_authenticated_user() -> None:
    client = get_client()

    response = client.post("/self/sessions/sess_missing/revoke")

    assert response.status_code == 401
    assert response.json()["error_code"] == "token_expired"


def test_self_revoke_returns_403_when_current_auth_context_is_already_revoked() -> None:
    client = get_client()
    tokens = login_as(client, username="alice", password="secret", device_id="device_revoked")

    logout = client.post(
        "/logout",
        json={
            "refresh_token": tokens["refresh_token"],
            "device_id": "device_revoked",
        },
    )
    assert logout.status_code == 200

    response = client.post(
        "/self/sessions/sess_any/revoke",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 403
    assert response.json()["error_code"] == "revoked"
