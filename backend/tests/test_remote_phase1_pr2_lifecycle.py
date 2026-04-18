from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import sys
from pathlib import Path

import pytest
import yaml
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
from app.models import AuditLog, EndUserSession, RefreshToken, UserDevice

OPENAPI_PATH = ROOT / 'remote' / 'remote-shared' / 'openapi' / 'remote-auth-v1.yaml'
REFRESH_SUCCESS_FIXTURE = ROOT / 'remote' / 'remote-shared' / 'scripts' / 'compat-harness' / 'fixtures' / 'refresh-success.json'
LOGOUT_SUCCESS_FIXTURE = ROOT / 'remote' / 'remote-shared' / 'scripts' / 'compat-harness' / 'fixtures' / 'logout-success.json'
ME_SUCCESS_FIXTURE = ROOT / 'remote' / 'remote-shared' / 'scripts' / 'compat-harness' / 'fixtures' / 'me-success.json'
DEVICE_MISMATCH_FIXTURE = ROOT / 'remote' / 'remote-shared' / 'scripts' / 'compat-harness' / 'fixtures' / 'error-device-mismatch.json'
REVOKED_FIXTURE = ROOT / 'remote' / 'remote-shared' / 'scripts' / 'compat-harness' / 'fixtures' / 'error-revoked.json'
MINIMUM_VERSION_FIXTURE = ROOT / 'remote' / 'remote-shared' / 'scripts' / 'compat-harness' / 'fixtures' / 'error-minimum-version-required.json'


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / 'remote_pr12.sqlite3'
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


def login_success(client: TestClient, *, device_id: str = 'device_abc', client_version: str = '0.2.0') -> dict:
    response = client.post(
        '/login',
        json={'username': 'alice', 'password': 'secret', 'device_id': device_id, 'client_version': client_version},
        headers={'X-Request-ID': 'req-pr12'},
    )
    assert response.status_code == 200
    return response.json()


def test_refresh_rotates_token_and_matches_contract_shape() -> None:
    fixture = json.loads(REFRESH_SUCCESS_FIXTURE.read_text(encoding='utf-8'))
    client = get_client()
    login_payload = login_success(client)

    response = client.post(
        '/refresh',
        json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_abc', 'client_version': '0.2.0'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert set(fixture.keys()).issubset(payload.keys())
    assert payload['token_type'] == fixture['token_type']
    assert payload['device_status'] == fixture['device_status']
    assert payload['refresh_token'] != login_payload['refresh_token']
    assert payload['access_token'] != login_payload['access_token']

    with session_scope() as session:
        session_row = session.query(EndUserSession).one()
        assert session_row.revoked_at is None
        tokens = session.query(RefreshToken).order_by(RefreshToken.id.asc()).all()
        assert len(tokens) == 2
        assert tokens[0].revoked_at is not None
        assert tokens[0].revoke_reason == 'rotated'
        assert tokens[1].revoked_at is None


def test_refresh_old_token_and_logout_revoke_session() -> None:
    revoked_fixture = json.loads(REVOKED_FIXTURE.read_text(encoding='utf-8'))
    logout_fixture = json.loads(LOGOUT_SUCCESS_FIXTURE.read_text(encoding='utf-8'))
    client = get_client()
    login_payload = login_success(client)

    refresh_response = client.post(
        '/refresh',
        json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_abc', 'client_version': '0.2.0'},
    )
    assert refresh_response.status_code == 200
    rotated = refresh_response.json()

    old_refresh = client.post(
        '/refresh',
        json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_abc', 'client_version': '0.2.0'},
    )
    assert old_refresh.status_code == 403
    assert old_refresh.json()['error_code'] == revoked_fixture['error_code']
    assert old_refresh.json()['message'] == revoked_fixture['message']

    logout_response = client.post('/logout', json={'refresh_token': rotated['refresh_token'], 'device_id': 'device_abc'})
    assert logout_response.status_code == 200
    assert logout_response.json() == logout_fixture

    revoked_refresh = client.post(
        '/refresh',
        json={'refresh_token': rotated['refresh_token'], 'device_id': 'device_abc', 'client_version': '0.2.0'},
    )
    assert revoked_refresh.status_code == 403
    assert revoked_refresh.json()['error_code'] == revoked_fixture['error_code']

    me_after_logout = client.get('/me', headers={'Authorization': f"Bearer {rotated['access_token']}"})
    assert me_after_logout.status_code == 403
    assert me_after_logout.json()['error_code'] == revoked_fixture['error_code']

    with session_scope() as session:
        session_row = session.query(EndUserSession).one()
        assert session_row.revoked_at is not None
        assert session_row.auth_state == 'revoked:logout'
        assert session.query(RefreshToken).filter(RefreshToken.revoked_at.is_(None)).count() == 0


def test_old_access_token_is_invalid_after_refresh_rotation() -> None:
    client = get_client()
    login_payload = login_success(client)

    refresh_response = client.post(
        '/refresh',
        json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_abc', 'client_version': '0.2.0'},
    )
    assert refresh_response.status_code == 200
    rotated = refresh_response.json()

    old_me = client.get('/me', headers={'Authorization': f"Bearer {login_payload['access_token']}"})
    assert old_me.status_code == 401
    assert old_me.json()['error_code'] == 'token_expired'

    current_me = client.get('/me', headers={'Authorization': f"Bearer {rotated['access_token']}"})
    assert current_me.status_code == 200


def test_logout_rejects_expired_refresh_token() -> None:
    client = get_client()
    login_payload = login_success(client)

    with session_scope() as session:
        token_row = session.query(RefreshToken).one()
        token_row.expires_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1)

    response = client.post('/logout', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_abc'})
    assert response.status_code == 401
    assert response.json()['error_code'] == 'token_expired'

    with session_scope() as session:
        session_row = session.query(EndUserSession).one()
        assert session_row.revoked_at is None


def test_me_returns_current_auth_context() -> None:
    fixture = json.loads(ME_SUCCESS_FIXTURE.read_text(encoding='utf-8'))
    client = get_client()
    login_payload = login_success(client)

    response = client.get('/me', headers={'Authorization': f"Bearer {login_payload['access_token']}"})
    assert response.status_code == 200
    payload = response.json()
    assert set(fixture.keys()).issubset(payload.keys())
    assert payload['user']['username'] == 'alice'
    assert payload['license_status'] == fixture['license_status']
    assert payload['device_status'] == fixture['device_status']
    assert payload['entitlements'] == fixture['entitlements']

    with session_scope() as session:
        binding = session.query(UserDevice).one()
        assert binding.last_auth_at is not None
        audit_events = [row.event_type for row in session.query(AuditLog).order_by(AuditLog.id.asc()).all()]
        assert 'auth_me_succeeded' in audit_events


def test_login_and_refresh_reject_different_device_binding() -> None:
    fixture = json.loads(DEVICE_MISMATCH_FIXTURE.read_text(encoding='utf-8'))
    client = get_client()
    login_payload = login_success(client)

    login_mismatch = client.post(
        '/login',
        json={'username': 'alice', 'password': 'secret', 'device_id': 'device_other', 'client_version': '0.2.0'},
    )
    assert login_mismatch.status_code == 403
    assert login_mismatch.json()['error_code'] == fixture['error_code']
    assert login_mismatch.json()['message'] == fixture['message']
    assert login_mismatch.json()['details'] == {'device_id': 'device_other'}

    refresh_mismatch = client.post(
        '/refresh',
        json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_other', 'client_version': '0.2.0'},
    )
    assert refresh_mismatch.status_code == 403
    assert refresh_mismatch.json()['error_code'] == fixture['error_code']
    assert refresh_mismatch.json()['message'] == fixture['message']

    logout_mismatch = client.post('/logout', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_other'})
    assert logout_mismatch.status_code == 403
    assert logout_mismatch.json()['error_code'] == fixture['error_code']
    assert logout_mismatch.json()['message'] == fixture['message']


def test_refresh_minimum_version_gate_uses_frozen_error_shape() -> None:
    fixture = json.loads(MINIMUM_VERSION_FIXTURE.read_text(encoding='utf-8'))
    client = get_client()
    login_payload = login_success(client)

    response = client.post(
        '/refresh',
        json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_abc', 'client_version': '0.1.0'},
    )
    assert response.status_code == 403
    assert response.json() == fixture


def test_refresh_rate_limit_blocks_after_threshold() -> None:
    client = get_client()
    login_success(client)
    for _ in range(5):
        response = client.post(
            '/refresh',
            json={'refresh_token': 'refresh_invalid', 'device_id': 'device_abc', 'client_version': '0.2.0'},
        )
        assert response.status_code == 401
    blocked = client.post(
        '/refresh',
        json={'refresh_token': 'refresh_invalid', 'device_id': 'device_abc', 'client_version': '0.2.0'},
    )
    assert blocked.status_code == 429
    assert blocked.json()['error_code'] == 'too_many_requests'


def test_refresh_me_and_logout_align_with_openapi_required_fields() -> None:
    spec = yaml.safe_load(OPENAPI_PATH.read_text(encoding='utf-8'))
    refresh_required = spec['components']['schemas']['AuthSuccessResponse']['required']
    me_required = spec['components']['schemas']['MeResponse']['required']
    logout_required = spec['components']['schemas']['LogoutResponse']['required']
    client = get_client()
    login_payload = login_success(client)

    refresh_response = client.post(
        '/refresh',
        json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_abc', 'client_version': '0.2.0'},
    )
    refresh_payload = refresh_response.json()
    for field in refresh_required:
        assert field in refresh_payload

    me_response = client.get('/me', headers={'Authorization': f"Bearer {refresh_payload['access_token']}"})
    me_payload = me_response.json()
    for field in me_required:
        assert field in me_payload

    logout_response = client.post('/logout', json={'refresh_token': refresh_payload['refresh_token'], 'device_id': 'device_abc'})
    logout_payload = logout_response.json()
    for field in logout_required:
        assert field in logout_payload


def test_refresh_and_me_emit_request_tracing_headers_and_audit_rows() -> None:
    client = get_client()
    login_payload = login_success(client)

    refresh_response = client.post(
        '/refresh',
        json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_abc', 'client_version': '0.2.0'},
        headers={'X-Request-ID': 'req-refresh'},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.headers['X-Request-ID'] == 'req-refresh'
    assert refresh_response.headers['X-Trace-ID'] == 'req-refresh'

    me_response = client.get('/me', headers={'Authorization': f"Bearer {refresh_response.json()['access_token']}", 'X-Request-ID': 'req-me'})
    assert me_response.status_code == 200
    assert me_response.headers['X-Request-ID'] == 'req-me'
    assert me_response.headers['X-Trace-ID'] == 'req-me'

    with session_scope() as session:
        audits = session.query(AuditLog).order_by(AuditLog.id.asc()).all()
        assert any(item.event_type == 'auth_refresh_succeeded' and item.request_id == 'req-refresh' for item in audits)
        assert any(item.event_type == 'auth_me_succeeded' and item.request_id == 'req-me' for item in audits)
