from __future__ import annotations

from datetime import datetime, timedelta
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
from app.models import AdminUser, User


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / 'remote_pr22.sqlite3'
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


def seed_end_user(client: TestClient, *, device_id: str = 'device_pr22') -> dict:
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': device_id, 'client_version': '0.2.0'})
    assert response.status_code == 200
    return response.json()


def admin_token(client: TestClient, *, username: str = 'admin', password: str = 'admin-secret') -> str:
    response = client.post('/admin/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json()['access_token']


def managed_user_id() -> str:
    with session_scope() as session:
        user = session.query(User).filter_by(username='alice').one()
        return f'u_{user.id}'


def test_admin_users_list_and_detail_return_real_user_context() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)
    target_user_id = managed_user_id()

    listing = client.get('/admin/users', headers={'Authorization': f'Bearer {token}'})
    assert listing.status_code == 200
    payload = listing.json()
    assert payload['total'] >= 1
    alice = next(item for item in payload['items'] if item['username'] == 'alice')
    assert alice['id'] == target_user_id
    assert alice['license_status'] == 'active'

    detail = client.get(f'/admin/users/{target_user_id}', headers={'Authorization': f'Bearer {token}'})
    assert detail.status_code == 200
    assert detail.json()['entitlements'] == ['dashboard:view', 'publish:run']


def test_admin_user_patch_updates_profile_and_entitlements() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)
    target_user_id = managed_user_id()

    response = client.patch(
        f'/admin/users/{target_user_id}',
        json={
            'display_name': 'Alice Remote',
            'license_expires_at': (datetime.utcnow() + timedelta(days=90)).isoformat(),
            'entitlements': ['dashboard:view', 'auth:admin'],
        },
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['display_name'] == 'Alice Remote'
    assert payload['entitlements'] == ['dashboard:view', 'auth:admin']


def test_admin_user_revoke_and_restore_change_end_user_auth() -> None:
    client = get_client()
    login_payload = seed_end_user(client)
    token = admin_token(client)
    target_user_id = managed_user_id()

    revoke = client.post(f'/admin/users/{target_user_id}/revoke', headers={'Authorization': f'Bearer {token}'})
    assert revoke.status_code == 200
    refresh = client.post('/refresh', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_pr22', 'client_version': '0.2.0'})
    assert refresh.status_code == 403
    assert refresh.json()['error_code'] == 'revoked'

    restore = client.post(f'/admin/users/{target_user_id}/restore', headers={'Authorization': f'Bearer {token}'})
    assert restore.status_code == 200
    relogin = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_pr22', 'client_version': '0.2.0'})
    assert relogin.status_code == 200


def test_support_readonly_cannot_patch_or_revoke_users() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client, username='support', password='support-secret')
    target_user_id = managed_user_id()

    patch = client.patch(
        f'/admin/users/{target_user_id}',
        json={'display_name': 'Should Fail'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert patch.status_code == 403
    assert patch.json()['error_code'] == 'forbidden'

    revoke = client.post(f'/admin/users/{target_user_id}/revoke', headers={'Authorization': f'Bearer {token}'})
    assert revoke.status_code == 403
    assert revoke.json()['error_code'] == 'forbidden'


def test_admin_user_detail_not_found_uses_frozen_error_code() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)

    response = client.get('/admin/users/u_9999', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
    assert response.json()['error_code'] == 'not_found'


def test_admin_user_detail_rejects_malformed_user_id() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)

    response = client.get('/admin/users/not-a-user', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
    assert response.json()['error_code'] == 'not_found'
