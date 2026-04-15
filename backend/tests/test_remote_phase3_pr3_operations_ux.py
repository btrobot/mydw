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
    db_path = tmp_path / 'remote_pr33.sqlite3'
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


def seed_end_user(client: TestClient, *, username: str = 'alice', password: str = 'secret', device_id: str = 'device_pr33_a') -> None:
    response = client.post('/login', json={'username': username, 'password': password, 'device_id': device_id, 'client_version': '0.2.0'})
    assert response.status_code == 200


def admin_token(client: TestClient, *, username: str = 'admin', password: str = 'admin-secret') -> str:
    response = client.post('/admin/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json()['access_token']


def ensure_user(username: str, *, password: str, display_name: str, status: str = 'active', license_status: str = 'active') -> str:
    with session_scope() as session:
        user = session.query(User).filter_by(username=username).one_or_none()
        if user is None:
            user = User(username=username, display_name=display_name, email=f'{username}@example.com', status=status, tenant_id='tenant_1')
            session.add(user)
            session.flush()
            session.add(UserCredential(user_id=user.id, password_hash=hash_password(password)))
            session.add(License(user_id=user.id, license_status=license_status))
        else:
            user.display_name = display_name
            user.status = status
            if user.license is None:
                session.add(License(user_id=user.id, license_status=license_status))
            else:
                user.license.license_status = license_status
        session.flush()
        return f'u_{user.id}'


def test_admin_users_filters_support_query_status_and_license_status() -> None:
    client = get_client()
    seed_end_user(client, username='alice', device_id='device_pr33_user_a')
    bob_id = ensure_user('bob', password='bob-secret', display_name='Bob Remote', status='disabled', license_status='revoked')
    token = admin_token(client)

    filtered = client.get(
        '/admin/users',
        params={'q': 'bob', 'status': 'disabled', 'license_status': 'revoked', 'limit': 10, 'offset': 0},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert filtered.status_code == 200
    payload = filtered.json()
    assert payload['total'] >= 1
    assert any(item['id'] == bob_id for item in payload['items'])
    assert all(item['status'] == 'disabled' for item in payload['items'])
    assert all(item['license_status'] == 'revoked' for item in payload['items'])


def test_admin_devices_filters_support_query_status_and_user() -> None:
    client = get_client()
    seed_end_user(client, username='alice', device_id='device_pr33_device_a')
    bob_id = ensure_user('bob', password='bob-secret', display_name='Bob Device')
    seed_end_user(client, username='bob', password='bob-secret', device_id='device_pr33_device_b')
    token = admin_token(client)

    disable = client.post('/admin/devices/device_pr33_device_b/disable', headers={'Authorization': f'Bearer {token}'})
    assert disable.status_code == 200

    by_status = client.get(
        '/admin/devices',
        params={'device_status': 'disabled', 'limit': 10, 'offset': 0},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert by_status.status_code == 200
    assert any(item['device_id'] == 'device_pr33_device_b' for item in by_status.json()['items'])

    by_user = client.get(
        '/admin/devices',
        params={'user_id': bob_id, 'limit': 10, 'offset': 0},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert by_user.status_code == 200
    assert all(item['user_id'] == bob_id for item in by_user.json()['items'])

    by_query = client.get(
        '/admin/devices',
        params={'q': 'device_pr33_device_b', 'limit': 10, 'offset': 0},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert by_query.status_code == 200
    assert by_query.json()['items'][0]['device_id'] == 'device_pr33_device_b'


def test_admin_sessions_filters_support_query_state_user_and_device() -> None:
    client = get_client()
    seed_end_user(client, username='alice', device_id='device_pr33_session_a')
    bob_id = ensure_user('bob', password='bob-secret', display_name='Bob Session')
    seed_end_user(client, username='bob', password='bob-secret', device_id='device_pr33_session_b')
    token = admin_token(client)

    sessions = client.get('/admin/sessions', headers={'Authorization': f'Bearer {token}'}).json()['items']
    target = next(item for item in sessions if item['device_id'] == 'device_pr33_session_a')
    revoke = client.post(f"/admin/sessions/{target['session_id']}/revoke", headers={'Authorization': f'Bearer {token}'})
    assert revoke.status_code == 200

    by_user = client.get(
        '/admin/sessions',
        params={'user_id': bob_id, 'limit': 10, 'offset': 0},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert by_user.status_code == 200
    assert all(item['user_id'] == bob_id for item in by_user.json()['items'])

    by_device = client.get(
        '/admin/sessions',
        params={'device_id': 'device_pr33_session_b', 'limit': 10, 'offset': 0},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert by_device.status_code == 200
    assert all(item['device_id'] == 'device_pr33_session_b' for item in by_device.json()['items'])

    by_state = client.get(
        '/admin/sessions',
        params={'auth_state': 'authenticated_active', 'limit': 10, 'offset': 0},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert by_state.status_code == 200
    assert all(item['auth_state'] == 'authenticated_active' for item in by_state.json()['items'])

    by_query = client.get(
        '/admin/sessions',
        params={'q': 'device_pr33_session_a', 'limit': 10, 'offset': 0},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert by_query.status_code == 200
    assert all(item['device_id'] == 'device_pr33_session_a' for item in by_query.json()['items'])
