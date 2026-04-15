from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
REMOTE_BACKEND_ROOT = ROOT / 'remote' / 'remote-backend'
if str(REMOTE_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(REMOTE_BACKEND_ROOT))

from app.api.admin import admin_login_rate_limiter
from app.api.auth import login_rate_limiter, refresh_rate_limiter
from app.core.config import reset_settings_cache
from app.core.db import reset_db_state, session_scope
from app.main import create_app
from app.migrations.runner import downgrade, upgrade
from app.models import AuditLog
from app.services.admin_authz import (
    ADMIN_PERMISSION_AUDIT_READ,
    ADMIN_PERMISSION_DEVICES_READ,
    ADMIN_PERMISSION_DEVICES_WRITE,
    ADMIN_PERMISSION_METRICS_READ,
    ADMIN_PERMISSION_SESSIONS_READ,
    ADMIN_PERMISSION_SESSIONS_REVOKE,
    ADMIN_PERMISSION_SESSION_READ,
    ADMIN_PERMISSION_USERS_READ,
    ADMIN_PERMISSION_USERS_WRITE,
    ADMIN_PERMISSION_MATRIX,
    ADMIN_READ_PERMISSIONS,
    ADMIN_WRITE_PERMISSIONS,
    ALL_ADMIN_PERMISSIONS,
    AdminPermissionError,
    require_permission,
)


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / 'remote_pr31.sqlite3'
    monkeypatch.setenv('REMOTE_BACKEND_DATABASE_URL', f'sqlite:///{db_path.as_posix()}')
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


def seed_end_user(client: TestClient, *, device_id: str = 'device_pr31') -> None:
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': device_id, 'client_version': '0.2.0'})
    assert response.status_code == 200


def admin_token(client: TestClient, *, username: str, password: str) -> str:
    response = client.post('/admin/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json()['access_token']


def first_user_id(client: TestClient, token: str) -> str:
    listing = client.get('/admin/users', headers={'Authorization': f'Bearer {token}'})
    assert listing.status_code == 200
    return next(item['id'] for item in listing.json()['items'] if item['username'] == 'alice')


def first_session_id(client: TestClient, token: str) -> str:
    sessions = client.get('/admin/sessions', headers={'Authorization': f'Bearer {token}'})
    assert sessions.status_code == 200
    return next(item['session_id'] for item in sessions.json()['items'] if item['device_id'] == 'device_pr31')


def first_device_id(client: TestClient, token: str) -> str:
    devices = client.get('/admin/devices', headers={'Authorization': f'Bearer {token}'})
    assert devices.status_code == 200
    return next(item['device_id'] for item in devices.json()['items'] if item['device_id'] == 'device_pr31')


def test_permission_matrix_covers_super_admin_and_rejects_disallowed_scope() -> None:
    assert ALL_ADMIN_PERMISSIONS == {
        ADMIN_PERMISSION_SESSION_READ,
        ADMIN_PERMISSION_USERS_READ,
        ADMIN_PERMISSION_USERS_WRITE,
        ADMIN_PERMISSION_DEVICES_READ,
        ADMIN_PERMISSION_DEVICES_WRITE,
        ADMIN_PERMISSION_SESSIONS_READ,
        ADMIN_PERMISSION_SESSIONS_REVOKE,
        ADMIN_PERMISSION_AUDIT_READ,
        ADMIN_PERMISSION_METRICS_READ,
    }
    assert ADMIN_PERMISSION_MATRIX['super_admin'].permissions == ALL_ADMIN_PERMISSIONS
    assert ADMIN_PERMISSION_MATRIX['auth_admin'].permissions == ALL_ADMIN_PERMISSIONS
    assert ADMIN_PERMISSION_MATRIX['support_readonly'].permissions == ADMIN_READ_PERMISSIONS
    assert ADMIN_READ_PERMISSIONS.isdisjoint(ADMIN_WRITE_PERMISSIONS)

    for permission in ALL_ADMIN_PERMISSIONS:
        assert require_permission('super_admin', permission).role == 'super_admin'

    with pytest.raises(AdminPermissionError):
        require_permission('support_readonly', 'users.write')

    with pytest.raises(AdminPermissionError):
        require_permission('unknown_role', 'users.read')


def test_support_readonly_can_only_read_control_plane_surfaces() -> None:
    client = get_client()
    seed_end_user(client)
    support = admin_token(client, username='support', password='support-secret')
    user_id = first_user_id(client, support)
    session_id = first_session_id(client, support)
    device_id = first_device_id(client, support)

    assert client.get('/admin/session', headers={'Authorization': f'Bearer {support}'}).status_code == 200
    assert client.get('/admin/users', headers={'Authorization': f'Bearer {support}'}).status_code == 200
    assert client.get(f'/admin/users/{user_id}', headers={'Authorization': f'Bearer {support}'}).status_code == 200
    assert client.get('/admin/devices', headers={'Authorization': f'Bearer {support}'}).status_code == 200
    assert client.get('/admin/sessions', headers={'Authorization': f'Bearer {support}'}).status_code == 200
    assert client.get('/admin/audit-logs', headers={'Authorization': f'Bearer {support}'}).status_code == 200
    assert client.get('/admin/metrics/summary', headers={'Authorization': f'Bearer {support}'}).status_code == 200

    patch = client.patch(
        f'/admin/users/{user_id}',
        json={'display_name': 'Nope'},
        headers={'Authorization': f'Bearer {support}'},
    )
    assert patch.status_code == 403
    assert patch.json()['details']['required_permission'] == 'users.write'

    revoke_session = client.post(
        f'/admin/sessions/{session_id}/revoke',
        headers={'Authorization': f'Bearer {support}'},
    )
    assert revoke_session.status_code == 403
    assert revoke_session.json()['details']['required_permission'] == 'sessions.revoke'

    unbind_device = client.post(
        f'/admin/devices/{device_id}/unbind',
        headers={'Authorization': f'Bearer {support}'},
    )
    assert unbind_device.status_code == 403
    assert unbind_device.json()['details']['required_permission'] == 'devices.write'

    disable_device = client.post(
        f'/admin/devices/{device_id}/disable',
        headers={'Authorization': f'Bearer {support}'},
    )
    assert disable_device.status_code == 403
    assert disable_device.json()['details']['required_permission'] == 'devices.write'

    rebind_device = client.post(
        f'/admin/devices/{device_id}/rebind',
        json={'user_id': user_id},
        headers={'Authorization': f'Bearer {support}'},
    )
    assert rebind_device.status_code == 403
    assert rebind_device.json()['details']['required_permission'] == 'devices.write'


def test_auth_admin_can_execute_destructive_actions_with_actor_audit() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client, username='auth-admin', password='auth-admin-secret')
    user_id = first_user_id(client, token)
    session_id = first_session_id(client, token)

    revoke_user = client.post(
        f'/admin/users/{user_id}/revoke',
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-rbac-user'},
    )
    assert revoke_user.status_code == 200

    restore_user = client.post(
        f'/admin/users/{user_id}/restore',
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-rbac-restore'},
    )
    assert restore_user.status_code == 200

    revoke_session = client.post(
        f'/admin/sessions/{session_id}/revoke',
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-rbac-session'},
    )
    assert revoke_session.status_code == 200

    with session_scope() as session:
        audits = session.query(AuditLog).order_by(AuditLog.id.asc()).all()
        assert any(row.event_type == 'authorization_user_revoked' and row.actor_id == 'admin_2' and row.target_user_id is not None for row in audits)
        assert any(row.event_type == 'authorization_user_restored' and row.actor_id == 'admin_2' for row in audits)
        assert any(row.event_type == 'admin_session_revoked' and row.actor_id == 'admin_2' and row.target_session_id == session_id and row.request_id == 'req-rbac-session' for row in audits)
        assert any(row.event_type == 'admin_authorization_checked' and row.actor_id == 'admin_2' for row in audits)


def test_super_admin_can_execute_full_surface_and_write_aggregate_user_audit() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client, username='admin', password='admin-secret')
    user_id = first_user_id(client, token)
    session_id = first_session_id(client, token)

    assert client.get('/admin/session', headers={'Authorization': f'Bearer {token}'}).status_code == 200
    assert client.get('/admin/users', headers={'Authorization': f'Bearer {token}'}).status_code == 200
    assert client.get('/admin/devices', headers={'Authorization': f'Bearer {token}'}).status_code == 200
    assert client.get('/admin/sessions', headers={'Authorization': f'Bearer {token}'}).status_code == 200
    assert client.get('/admin/audit-logs', headers={'Authorization': f'Bearer {token}'}).status_code == 200
    assert client.get('/admin/metrics/summary', headers={'Authorization': f'Bearer {token}'}).status_code == 200

    update = client.patch(
        f'/admin/users/{user_id}',
        json={
            'display_name': 'Alice Super Admin',
            'license_status': 'revoked',
            'entitlements': ['dashboard:view', 'support:read'],
        },
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-super-update'},
    )
    assert update.status_code == 200
    assert update.json()['display_name'] == 'Alice Super Admin'

    revoke_session = client.post(
        f'/admin/sessions/{session_id}/revoke',
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-super-session'},
    )
    assert revoke_session.status_code == 200

    with session_scope() as session:
        audits = session.query(AuditLog).order_by(AuditLog.id.asc()).all()
        aggregate_update = next(
            row
            for row in audits
            if row.event_type == 'admin_user_updated'
            and row.actor_id == 'admin_1'
            and row.target_user_id == user_id.removeprefix('u_')
            and row.request_id == 'req-super-update'
        )
        update_details = json.loads(aggregate_update.details_json)
        assert update_details['fields']['display_name'] == 'Alice Super Admin'
        assert update_details['fields']['license_status'] == 'revoked'
        assert update_details['fields']['entitlements'] == ['dashboard:view', 'support:read']

        assert any(
            row.event_type == 'authorization_user_revoked'
            and row.actor_id == 'admin_1'
            and row.target_user_id == user_id.removeprefix('u_')
            and row.request_id == 'req-super-update'
            for row in audits
        )
        assert any(
            row.event_type == 'admin_session_revoked'
            and row.actor_id == 'admin_1'
            and row.target_session_id == session_id
            and row.request_id == 'req-super-session'
            for row in audits
        )
