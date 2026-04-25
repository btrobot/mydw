from __future__ import annotations

from datetime import datetime
from types import MethodType, SimpleNamespace

from app.schemas.admin import AdminActionResponse
from app.services.admin_service import AdminService
from app.services.admin_authz import ADMIN_PERMISSION_USERS_READ, ADMIN_PERMISSION_USERS_WRITE


class FakeDB:
    def __init__(self) -> None:
        self.commit_count = 0

    def commit(self) -> None:
        self.commit_count += 1


class FakeAdminRepository:
    def __init__(self, *, users: list[SimpleNamespace], total: int) -> None:
        self.db = FakeDB()
        self.users = users
        self.total = total
        self.count_users_calls: list[dict[str, object]] = []
        self.list_users_calls: list[dict[str, object]] = []
        self.audit_logs: list[dict[str, object]] = []

    def count_users(self, **kwargs):
        self.count_users_calls.append(kwargs)
        return self.total

    def list_users(self, **kwargs):
        self.list_users_calls.append(kwargs)
        return self.users

    def write_audit_log(self, **kwargs) -> None:
        self.audit_logs.append(kwargs)


class RecordingUserControl:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, str, str]] = []

    def revoke_user(self, user_id: int, *, actor_type: str, actor_id: str) -> None:
        self.calls.append(("revoke", user_id, actor_type, actor_id))

    def restore_user(self, user_id: int, *, actor_type: str, actor_id: str) -> None:
        self.calls.append(("restore", user_id, actor_type, actor_id))


def _make_user(*, user_id: int = 1) -> SimpleNamespace:
    last_seen_at = datetime(2026, 4, 29, 12, 0, 0)
    license_expires_at = datetime(2026, 7, 1, 0, 0, 0)
    return SimpleNamespace(
        id=user_id,
        username="alice",
        display_name="Alice",
        email="alice@example.com",
        tenant_id="tenant_1",
        status="active",
        license=SimpleNamespace(license_status="active", expires_at=license_expires_at),
        entitlements=[SimpleNamespace(entitlement="dashboard:view"), SimpleNamespace(entitlement="publish:run")],
        bindings=[SimpleNamespace(binding_status="bound"), SimpleNamespace(binding_status="unbound")],
        sessions=[SimpleNamespace(last_seen_at=last_seen_at)],
    )


def _make_service(repository: FakeAdminRepository) -> AdminService:
    service = AdminService(repository)
    service.user_control = RecordingUserControl()

    admin_user = SimpleNamespace(id=7, role="super_admin", status="active")

    def _require_admin_session(self, access_token: str, *, permission: str):
        assert access_token == "token"
        assert permission in {ADMIN_PERMISSION_USERS_READ, ADMIN_PERMISSION_USERS_WRITE}
        return admin_user, SimpleNamespace(session_id="admin_sess_1")

    service._require_admin_session = MethodType(_require_admin_session, service)
    return service


def test_list_users_returns_items_and_forwards_filters() -> None:
    user = _make_user()
    repository = FakeAdminRepository(users=[user], total=1)
    service = _make_service(repository)

    result = service.list_users(
        "token",
        q="alice",
        status="active",
        license_status="active",
        limit=25,
        offset=10,
    )

    assert result.total == 1
    assert len(result.items) == 1
    assert result.items[0].id == "u_1"
    assert result.items[0].device_count == 1
    assert result.items[0].entitlements == ["dashboard:view", "publish:run"]
    assert repository.count_users_calls == [
        {"q": "alice", "status": "active", "license_status": "active"}
    ]
    assert repository.list_users_calls == [
        {"q": "alice", "status": "active", "license_status": "active", "limit": 25, "offset": 10}
    ]
    assert repository.audit_logs[-1]["event_type"] == "admin_users_listed"
    assert repository.db.commit_count == 1


def test_revoke_user_calls_user_control_with_admin_actor() -> None:
    user = _make_user()
    repository = FakeAdminRepository(users=[user], total=1)
    service = _make_service(repository)
    service._load_target_user = MethodType(lambda self, user_id: user, service)

    result = service.revoke_user("token", "u_1")

    assert result == AdminActionResponse(success=True)
    assert service.user_control.calls == [("revoke", 1, "admin", "admin_7")]
    assert repository.db.commit_count == 1


def test_restore_user_calls_user_control_with_admin_actor() -> None:
    user = _make_user()
    repository = FakeAdminRepository(users=[user], total=1)
    service = _make_service(repository)
    service._load_target_user = MethodType(lambda self, user_id: user, service)

    result = service.restore_user("token", "u_1")

    assert result == AdminActionResponse(success=True)
    assert service.user_control.calls == [("restore", 1, "admin", "admin_7")]
    assert repository.db.commit_count == 1
