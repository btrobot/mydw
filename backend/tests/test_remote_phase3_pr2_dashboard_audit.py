from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
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
    db_path = tmp_path / 'remote_pr32.sqlite3'
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


def seed_end_user(client: TestClient, *, device_id: str = 'device_pr32') -> dict:
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': device_id, 'client_version': '0.2.0'})
    assert response.status_code == 200
    return response.json()


def admin_token(client: TestClient, *, username: str = 'admin', password: str = 'admin-secret') -> str:
    response = client.post('/admin/login', json={'username': username, 'password': password})
    assert response.status_code == 200
    return response.json()['access_token']


def current_user_id(client: TestClient, token: str) -> str:
    listing = client.get('/admin/users', headers={'Authorization': f'Bearer {token}'})
    assert listing.status_code == 200
    return next(item['id'] for item in listing.json()['items'] if item['username'] == 'alice')


def current_session_id(client: TestClient, token: str) -> str:
    sessions = client.get('/admin/sessions', headers={'Authorization': f'Bearer {token}'})
    assert sessions.status_code == 200
    return next(item['session_id'] for item in sessions.json()['items'] if item['device_id'] == 'device_pr32')


def test_admin_audit_logs_support_multidimensional_filters_pagination_and_trace_fields() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)
    user_id = current_user_id(client, token)
    raw_user_id = user_id.removeprefix('u_')
    session_id = current_session_id(client, token)

    revoke_user = client.post(
        f'/admin/users/{user_id}/revoke',
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-pr32-user-revoke'},
    )
    assert revoke_user.status_code == 200

    restore_user = client.post(
        f'/admin/users/{user_id}/restore',
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-pr32-user-restore'},
    )
    assert restore_user.status_code == 200

    revoke_session = client.post(
        f'/admin/sessions/{session_id}/revoke',
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-pr32-session-revoke'},
    )
    assert revoke_session.status_code == 200

    paged = client.get('/admin/audit-logs?actor_id=admin_1&limit=1&offset=0', headers={'Authorization': f'Bearer {token}'})
    assert paged.status_code == 200
    paged_payload = paged.json()
    assert paged_payload['total'] >= 3
    assert len(paged_payload['items']) == 1
    assert paged_payload['items'][0]['request_id'] is not None
    assert paged_payload['items'][0]['trace_id'] is not None

    filtered = client.get(
        f'/admin/audit-logs?event_type=authorization_user_revoked&actor_id=admin_1&target_user_id={raw_user_id}&limit=5&offset=0',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert filtered.status_code == 200
    filtered_payload = filtered.json()
    assert filtered_payload['total'] >= 1
    assert all(item['event_type'] == 'authorization_user_revoked' for item in filtered_payload['items'])
    assert all(item['actor_id'] == 'admin_1' for item in filtered_payload['items'])
    assert all(item['target_user_id'] == raw_user_id for item in filtered_payload['items'])

    session_filtered = client.get(
        f'/admin/audit-logs?event_type=admin_session_revoked&target_session_id={session_id}&limit=5&offset=0',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert session_filtered.status_code == 200
    session_payload = session_filtered.json()
    assert session_payload['total'] == 1
    assert session_payload['items'][0]['target_session_id'] == session_id
    assert session_payload['items'][0]['request_id'] == 'req-pr32-session-revoke'

    created_at_utc = datetime.fromisoformat(session_payload['items'][0]['created_at']).replace(tzinfo=timezone.utc)
    created_from_shanghai = created_at_utc.astimezone(timezone(timedelta(hours=8))).replace(second=0, microsecond=0)
    created_to_shanghai = created_from_shanghai + timedelta(minutes=1)
    timezone_filtered = client.get(
        '/admin/audit-logs',
        params={
            'event_type': 'admin_session_revoked',
            'target_session_id': session_id,
            'created_from': created_from_shanghai.isoformat(),
            'created_to': created_to_shanghai.isoformat(),
            'limit': 5,
            'offset': 0,
        },
        headers={'Authorization': f'Bearer {token}'},
    )
    assert timezone_filtered.status_code == 200
    assert timezone_filtered.json()['total'] == 1


def test_admin_metrics_summary_returns_recent_failure_and_destructive_event_summaries() -> None:
    client = get_client()
    seed_end_user(client)
    token = admin_token(client)
    user_id = current_user_id(client, token)
    session_id = current_session_id(client, token)

    failed_login = client.post(
        '/login',
        json={'username': 'alice', 'password': 'wrong', 'device_id': 'device_pr32', 'client_version': '0.2.0'},
        headers={'X-Request-ID': 'req-pr32-login-failed'},
    )
    assert failed_login.status_code == 401

    failed_admin_login = client.post(
        '/admin/login',
        json={'username': 'admin', 'password': 'wrong'},
        headers={'X-Request-ID': 'req-pr32-admin-login-failed'},
    )
    assert failed_admin_login.status_code == 401

    revoke_user = client.post(
        f'/admin/users/{user_id}/revoke',
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-pr32-metrics-revoke-user'},
    )
    assert revoke_user.status_code == 200

    revoke_session = client.post(
        f'/admin/sessions/{session_id}/revoke',
        headers={'Authorization': f'Bearer {token}', 'X-Request-ID': 'req-pr32-metrics-revoke-session'},
    )
    assert revoke_session.status_code == 200

    metrics = client.get('/admin/metrics/summary', headers={'Authorization': f'Bearer {token}'})
    assert metrics.status_code == 200
    payload = metrics.json()
    assert payload['login_failures'] >= 2
    assert payload['destructive_actions'] >= 2
    assert payload['generated_at']
    assert payload['recent_failures']
    assert payload['recent_destructive_actions']
    assert any(item['event_type'] in {'auth_login_failed', 'admin_login_failed'} for item in payload['recent_failures'])
    assert any(item['request_id'] in {'req-pr32-login-failed', 'req-pr32-admin-login-failed'} for item in payload['recent_failures'])
    assert any(item['event_type'] == 'authorization_user_revoked' for item in payload['recent_destructive_actions'])
    assert any(item['event_type'] == 'admin_session_revoked' for item in payload['recent_destructive_actions'])
    assert any(item['request_id'] == 'req-pr32-metrics-revoke-user' for item in payload['recent_destructive_actions'])
