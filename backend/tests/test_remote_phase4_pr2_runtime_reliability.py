from __future__ import annotations

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
from app.core.security import hash_password
from app.main import create_app
from app.migrations.runner import downgrade, upgrade
from app.models import License, User, UserCredential


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / 'remote_pr42.sqlite3'
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


def seed_end_user(client: TestClient, *, username: str = 'alice', password: str = 'secret', device_id: str) -> None:
    response = client.post('/login', json={'username': username, 'password': password, 'device_id': device_id, 'client_version': '0.2.0'})
    assert response.status_code == 200


def ensure_user(username: str, *, password: str, display_name: str, license_status: str = 'active') -> str:
    with session_scope() as session:
        user = session.query(User).filter_by(username=username).one_or_none()
        if user is None:
            user = User(username=username, display_name=display_name, email=f'{username}@example.com', status='active', tenant_id='tenant_1')
            session.add(user)
            session.flush()
            session.add(UserCredential(user_id=user.id, password_hash=hash_password(password)))
            session.add(License(user_id=user.id, license_status=license_status))
        return f'u_{user.id}'


def admin_token(client: TestClient) -> str:
    response = client.post('/admin/login', json={'username': 'admin', 'password': 'admin-secret'})
    assert response.status_code == 200
    return response.json()['access_token']


def test_filtered_totals_remain_global_when_limit_offset_are_used() -> None:
    client = get_client()
    seed_end_user(client, username='alice', device_id='device_pr42_a')
    ensure_user('bob', password='bob-secret', display_name='Bob Remote')
    seed_end_user(client, username='bob', password='bob-secret', device_id='device_pr42_b')
    token = admin_token(client)

    users = client.get('/admin/users', params={'limit': 1, 'offset': 0}, headers={'Authorization': f'Bearer {token}'})
    assert users.status_code == 200
    assert users.json()['total'] >= 2
    assert len(users.json()['items']) == 1

    devices = client.get('/admin/devices', params={'device_status': 'bound', 'limit': 1, 'offset': 0}, headers={'Authorization': f'Bearer {token}'})
    assert devices.status_code == 200
    assert devices.json()['total'] >= 2
    assert len(devices.json()['items']) == 1

    sessions = client.get('/admin/sessions', params={'auth_state': 'authenticated_active', 'limit': 1, 'offset': 0}, headers={'Authorization': f'Bearer {token}'})
    assert sessions.status_code == 200
    assert sessions.json()['total'] >= 2
    assert len(sessions.json()['items']) == 1


def test_metrics_recent_summaries_are_capped_to_latest_five_events() -> None:
    client = get_client()
    seed_end_user(client, username='alice', device_id='device_pr42_metrics')
    token = admin_token(client)

    users = client.get('/admin/users', headers={'Authorization': f'Bearer {token}'}).json()['items']
    user_id = next(item['id'] for item in users if item['username'] == 'alice')

    sessions = client.get('/admin/sessions', headers={'Authorization': f'Bearer {token}'}).json()['items']
    session_id = next(item['session_id'] for item in sessions if item['device_id'] == 'device_pr42_metrics')

    for idx in range(6):
        failed = client.post('/login', json={'username': f'ghost-{idx}', 'password': 'wrong', 'device_id': f'device_fail_{idx}', 'client_version': '0.2.0'})
        assert failed.status_code == 401

    for idx in range(3):
        revoke = client.post(f'/admin/users/{user_id}/revoke', headers={'Authorization': f'Bearer {token}', 'X-Request-ID': f'req-user-revoke-{idx}'})
        assert revoke.status_code == 200
        restore = client.post(f'/admin/users/{user_id}/restore', headers={'Authorization': f'Bearer {token}', 'X-Request-ID': f'req-user-restore-{idx}'})
        assert restore.status_code == 200
    revoke_session = client.post(f'/admin/sessions/{session_id}/revoke', headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-session-revoke'})
    assert revoke_session.status_code == 200
    disable_device = client.post('/admin/devices/device_pr42_metrics/disable', headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-device-disable'})
    assert disable_device.status_code == 200
    rebind_device = client.post(
        '/admin/devices/device_pr42_metrics/rebind',
        json={'user_id': user_id, 'client_version': '0.2.0'},
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-device-rebind'},
    )
    assert rebind_device.status_code == 200

    metrics = client.get('/admin/metrics/summary', headers={'Authorization': f'Bearer {token}'})
    assert metrics.status_code == 200
    payload = metrics.json()
    assert len(payload['recent_failures']) == 5
    assert len(payload['recent_destructive_actions']) == 5
