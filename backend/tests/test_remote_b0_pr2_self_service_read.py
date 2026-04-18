from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
from app.models import License, User, UserCredential, UserEntitlement


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "remote_b0_pr2.sqlite3"
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
                starts_at=datetime.now(UTC).replace(tzinfo=None),
                expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(days=30),
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


def test_self_routes_appear_in_runtime_openapi_and_self_me_uses_portal_schema() -> None:
    spec = create_app().openapi()

    for path in ["/self/me", "/self/devices", "/self/sessions", "/self/activity"]:
        assert path in spec["paths"]

    assert spec["paths"]["/self/me"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/SelfMeResponse"
    assert "tenant_id" not in spec["components"]["schemas"]["SelfUserIdentity"]["properties"]


def test_self_me_hides_tenant_id_while_legacy_me_keeps_compatibility() -> None:
    client = get_client()
    tokens = login_as(client, username="alice", password="secret", device_id="device_self")
    auth_header = {"Authorization": f"Bearer {tokens['access_token']}"}

    legacy = client.get("/me", headers=auth_header)
    assert legacy.status_code == 200
    assert legacy.json()["user"]["tenant_id"] == "tenant_1"

    self_me = client.get("/self/me", headers=auth_header)
    assert self_me.status_code == 200
    payload = self_me.json()
    assert payload["user"]["username"] == "alice"
    assert "tenant_id" not in payload["user"]


def test_self_devices_and_sessions_are_scoped_to_current_user() -> None:
    seed_user(username="bob", password="hunter2", tenant_id="tenant_2")
    client = get_client()
    alice_tokens = login_as(client, username="alice", password="secret", device_id="device_alice")
    bob_tokens = login_as(client, username="bob", password="hunter2", device_id="device_bob")

    alice_header = {"Authorization": f"Bearer {alice_tokens['access_token']}"}
    bob_header = {"Authorization": f"Bearer {bob_tokens['access_token']}"}

    alice_devices = client.get("/self/devices", headers=alice_header)
    alice_sessions = client.get("/self/sessions", headers=alice_header)
    bob_devices = client.get("/self/devices", headers=bob_header)

    assert alice_devices.status_code == 200
    assert alice_sessions.status_code == 200
    assert bob_devices.status_code == 200

    alice_device_ids = {item["device_id"] for item in alice_devices.json()["items"]}
    alice_session_device_ids = {item["device_id"] for item in alice_sessions.json()["items"]}
    bob_device_ids = {item["device_id"] for item in bob_devices.json()["items"]}

    assert "device_alice" in alice_device_ids
    assert "device_bob" not in alice_device_ids
    assert "device_alice" in alice_session_device_ids
    assert "device_bob" not in alice_session_device_ids
    assert bob_device_ids == {"device_bob"}


def test_self_activity_returns_portal_safe_projection_only() -> None:
    client = get_client()
    tokens = login_as(client, username="alice", password="secret", device_id="device_activity")
    refresh = client.post(
        "/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
            "device_id": "device_activity",
            "client_version": "0.2.0",
        },
    )
    assert refresh.status_code == 200, refresh.json()

    logout = client.post(
        "/logout",
        json={
            "refresh_token": refresh.json()["refresh_token"],
            "device_id": "device_activity",
        },
    )
    assert logout.status_code == 200, logout.json()

    relogin = login_as(client, username="alice", password="secret", device_id="device_activity")
    activity = client.get("/self/activity", headers={"Authorization": f"Bearer {relogin['access_token']}"})
    assert activity.status_code == 200
    payload = activity.json()
    assert payload["total"] >= 3

    allowed_keys = {"id", "event_type", "created_at", "summary", "device_id", "session_id"}
    allowed_event_types = {
        "login_succeeded",
        "login_failed",
        "session_refreshed",
        "session_revoked",
        "device_bound",
        "device_unbound",
    }
    assert payload["items"]
    event_types = set()
    for item in payload["items"]:
        assert set(item).issubset(allowed_keys)
        assert item["event_type"] in allowed_event_types
        assert "request_id" not in item
        assert "trace_id" not in item
        assert "actor_type" not in item
        event_types.add(item["event_type"])
    assert "session_revoked" in event_types
