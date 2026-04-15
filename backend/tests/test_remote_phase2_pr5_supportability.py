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
    db_path = tmp_path / 'remote_pr25.sqlite3'
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


def seed_end_user(client: TestClient, *, device_id: str = 'device_pr25') -> dict:
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': device_id, 'client_version': '0.2.0'})
    assert response.status_code == 200
    return response.json()


def admin_token(client: TestClient, *, username: str = 'admin', password: str = 'admin-secret') -> str:
    response = client.post('/admin/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json()['access_token']


def current_user_id(client: TestClient) -> str:
    listing = client.get('/admin/users', headers={'Authorization': f'Bearer {admin_token(client)}'})
    assert listing.status_code == 200
    return next(item['id'] for item in listing.json()['items'] if item['username'] == 'alice')


def current_session_id(client: TestClient, token: str) -> str:
    sessions = client.get('/admin/sessions', headers={'Authorization': f'Bearer {token}'})
    assert sessions.status_code == 200
    return next(item['session_id'] for item in sessions.json()['items'] if item['device_id'] == 'device_pr25')


def test_admin_audit_logs_can_filter_destructive_actions() -> None:
    client = get_client()
    login_payload = seed_end_user(client)
    token = admin_token(client)
    user_id = current_user_id(client)
    session_id = current_session_id(client, token)

    revoke_user = client.post(f'/admin/users/{user_id}/revoke', headers={'Authorization': f'Bearer {token}'})
    assert revoke_user.status_code == 200
    restore_user = client.post(f'/admin/users/{user_id}/restore', headers={'Authorization': f'Bearer {token}'})
    assert restore_user.status_code == 200
    revoke_session = client.post(f'/admin/sessions/{session_id}/revoke', headers={'Authorization': f'Bearer {token}'})
    assert revoke_session.status_code == 200

    audit = client.get('/admin/audit-logs', headers={'Authorization': f'Bearer {token}'})
    assert audit.status_code == 200
    payload = audit.json()
    event_types = {item['event_type'] for item in payload['items']}
    assert 'authorization_user_revoked' in event_types
    assert 'authorization_user_restored' in event_types
    assert 'admin_session_revoked' in event_types

    filtered = client.get('/admin/audit-logs?event_type=admin_session_revoked', headers={'Authorization': f'Bearer {token}'})
    assert filtered.status_code == 200
    assert filtered.json()['total'] >= 1
    assert all(item['event_type'] == 'admin_session_revoked' for item in filtered.json()['items'])


def test_admin_metrics_summary_returns_operational_counts() -> None:
    client = get_client()
    login_payload = seed_end_user(client)
    token = admin_token(client)
    user_id = current_user_id(client)
    session_id = current_session_id(client, token)

    client.post('/login', json={'username': 'alice', 'password': 'wrong', 'device_id': 'device_pr25', 'client_version': '0.2.0'})
    client.post(f'/admin/users/{user_id}/revoke', headers={'Authorization': f'Bearer {token}'})
    client.post(f'/admin/users/{user_id}/restore', headers={'Authorization': f'Bearer {token}'})
    client.post(f'/admin/sessions/{session_id}/revoke', headers={'Authorization': f'Bearer {token}'})

    metrics = client.get('/admin/metrics/summary', headers={'Authorization': f'Bearer {token}'})
    assert metrics.status_code == 200
    payload = metrics.json()
    assert payload['login_failures'] >= 1
    assert payload['destructive_actions'] >= 2
    assert payload['active_sessions'] >= 0


def test_support_readonly_can_view_audit_and_metrics() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client, username='support', password='support-secret')

    audit = client.get('/admin/audit-logs', headers={'Authorization': f'Bearer {token}'})
    assert audit.status_code == 200

    metrics = client.get('/admin/metrics/summary', headers={'Authorization': f'Bearer {token}'})
    assert metrics.status_code == 200


def test_admin_audit_logs_invalid_datetime_filter_returns_validation_payload() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)

    response = client.get('/admin/audit-logs?created_from=not-a-date', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 422
    assert 'detail' in response.json()
