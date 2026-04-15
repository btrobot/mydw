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
from app.core.db import reset_db_state
from app.main import create_app
from app.migrations.runner import downgrade, upgrade


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / 'remote_pr24.sqlite3'
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


def seed_end_user(client: TestClient, *, device_id: str = 'device_pr24') -> dict:
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': device_id, 'client_version': '0.2.0'})
    assert response.status_code == 200
    return response.json()


def admin_token(client: TestClient, *, username: str = 'admin', password: str = 'admin-secret') -> str:
    response = client.post('/admin/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json()['access_token']


def test_admin_sessions_list_returns_real_context() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)

    listing = client.get('/admin/sessions', headers={'Authorization': f'Bearer {token}'})
    assert listing.status_code == 200
    payload = listing.json()
    assert payload['total'] >= 1
    session_row = next(item for item in payload['items'] if item['device_id'] == 'device_pr24')
    assert session_row['auth_state'] == 'authenticated_active'
    assert session_row['user_id'].startswith('u_')


def test_admin_revoke_session_invalidates_me_and_refresh() -> None:
    client = get_client()
    login_payload = seed_end_user(client)
    token = admin_token(client)

    sessions = client.get('/admin/sessions', headers={'Authorization': f'Bearer {token}'}).json()['items']
    target = next(item for item in sessions if item['device_id'] == 'device_pr24')

    revoke = client.post(f"/admin/sessions/{target['session_id']}/revoke", headers={'Authorization': f'Bearer {token}'})
    assert revoke.status_code == 200

    me = client.get('/me', headers={'Authorization': f"Bearer {login_payload['access_token']}"})
    assert me.status_code == 403
    assert me.json()['error_code'] == 'revoked'

    refresh = client.post('/refresh', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_pr24', 'client_version': '0.2.0'})
    assert refresh.status_code == 403
    assert refresh.json()['error_code'] == 'revoked'


def test_support_readonly_cannot_revoke_session() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client, username='support', password='support-secret')
    sessions = client.get('/admin/sessions', headers={'Authorization': f'Bearer {token}'}).json()['items']
    target = next(item for item in sessions if item['device_id'] == 'device_pr24')

    revoke = client.post(f"/admin/sessions/{target['session_id']}/revoke", headers={'Authorization': f'Bearer {token}'})
    assert revoke.status_code == 403
    assert revoke.json()['error_code'] == 'forbidden'


def test_admin_revoke_session_not_found_uses_frozen_error_code() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)

    response = client.post('/admin/sessions/missing-session/revoke', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
    assert response.json()['error_code'] == 'not_found'
