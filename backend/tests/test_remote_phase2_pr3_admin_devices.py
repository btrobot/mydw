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
from app.main import create_app
from app.migrations.runner import downgrade, upgrade
from app.models import User, UserCredential
from app.core.security import hash_password


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / 'remote_pr23.sqlite3'
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


def seed_end_user(client: TestClient, *, username: str = 'alice', password: str = 'secret', device_id: str = 'device_pr23') -> dict:
    response = client.post('/login', json={'username': username, 'password': password, 'device_id': device_id, 'client_version': '0.2.0'})
    assert response.status_code == 200
    return response.json()


def admin_token(client: TestClient, *, username: str = 'admin', password: str = 'admin-secret') -> str:
    response = client.post('/admin/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json()['access_token']


def create_second_user() -> str:
    with session_scope() as session:
        if session.query(User).filter_by(username='bob').one_or_none() is None:
            user = User(username='bob', display_name='Bob', email='bob@example.com', status='active', tenant_id='tenant_1')
            session.add(user)
            session.flush()
            session.add(UserCredential(user_id=user.id, password_hash=hash_password('bob-secret')))
        user = session.query(User).filter_by(username='bob').one()
        return f'u_{user.id}'


def test_admin_devices_list_and_detail_return_real_context() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)

    listing = client.get('/admin/devices', headers={'Authorization': f'Bearer {token}'})
    assert listing.status_code == 200
    payload = listing.json()
    assert payload['total'] >= 1
    device = next(item for item in payload['items'] if item['device_id'] == 'device_pr23')
    assert device['device_status'] == 'bound'
    assert device['user_id'].startswith('u_')

    detail = client.get('/admin/devices/device_pr23', headers={'Authorization': f'Bearer {token}'})
    assert detail.status_code == 200
    assert detail.json()['device_id'] == 'device_pr23'


def test_admin_device_unbind_forces_device_mismatch() -> None:
    client = get_client()
    login_payload = seed_end_user(client)
    token = admin_token(client)

    response = client.post('/admin/devices/device_pr23/unbind', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200

    refresh = client.post('/refresh', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_pr23', 'client_version': '0.2.0'})
    assert refresh.status_code == 403
    assert refresh.json()['error_code'] == 'device_mismatch'


def test_admin_device_disable_forces_device_mismatch_until_rebind() -> None:
    client = get_client()
    login_payload = seed_end_user(client)
    token = admin_token(client)

    disable = client.post('/admin/devices/device_pr23/disable', headers={'Authorization': f'Bearer {token}'})
    assert disable.status_code == 200

    refresh = client.post('/refresh', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_pr23', 'client_version': '0.2.0'})
    assert refresh.status_code == 403
    assert refresh.json()['error_code'] == 'device_mismatch'

    rebind = client.post(
        '/admin/devices/device_pr23/rebind',
        json={'user_id': detail_user_id(client), 'client_version': '0.2.0'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert rebind.status_code == 200

    stale_refresh = client.post('/refresh', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_pr23', 'client_version': '0.2.0'})
    assert stale_refresh.status_code == 403
    assert stale_refresh.json()['error_code'] == 'revoked'

    relogin = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_pr23', 'client_version': '0.2.0'})
    assert relogin.status_code == 200


def detail_user_id(client: TestClient) -> str:
    with session_scope() as session:
        user = session.query(User).filter_by(username='alice').one()
        return f'u_{user.id}'


def test_admin_device_rebind_can_move_device_to_new_user() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)
    bob_id = create_second_user()

    response = client.post(
        '/admin/devices/device_pr23/rebind',
        json={'user_id': bob_id, 'client_version': '0.2.0'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200

    detail = client.get('/admin/devices/device_pr23', headers={'Authorization': f'Bearer {token}'})
    assert detail.status_code == 200
    assert detail.json()['user_id'] == bob_id


def test_support_readonly_cannot_unbind_or_disable_device() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client, username='support', password='support-secret')

    unbind = client.post('/admin/devices/device_pr23/unbind', headers={'Authorization': f'Bearer {token}'})
    assert unbind.status_code == 403
    assert unbind.json()['error_code'] == 'forbidden'

    disable = client.post('/admin/devices/device_pr23/disable', headers={'Authorization': f'Bearer {token}'})
    assert disable.status_code == 403
    assert disable.json()['error_code'] == 'forbidden'
