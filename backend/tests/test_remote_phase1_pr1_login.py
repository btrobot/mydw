from __future__ import annotations

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

from app.core.config import reset_settings_cache
from app.core.db import reset_db_state, session_scope
from app.api.admin import admin_login_rate_limiter
from app.api.auth import login_rate_limiter, refresh_rate_limiter
from app.main import create_app
from app.migrations.runner import downgrade, upgrade
from app.models import AuditLog, Device, EndUserSession, License, RefreshToken, User

OPENAPI_PATH = ROOT / 'remote' / 'remote-shared' / 'openapi' / 'remote-auth-v1.yaml'
LOGIN_SUCCESS_FIXTURE = ROOT / 'remote' / 'remote-shared' / 'scripts' / 'compat-harness' / 'fixtures' / 'login-success.json'
LOGIN_ERROR_FIXTURE = ROOT / 'remote' / 'remote-shared' / 'scripts' / 'compat-harness' / 'fixtures' / 'error-invalid-credentials.json'


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / 'remote_pr11.sqlite3'
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


def test_login_success_matches_frozen_contract_shape() -> None:
    fixture = json.loads(LOGIN_SUCCESS_FIXTURE.read_text(encoding='utf-8'))
    client = get_client()
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_abc', 'client_version': '0.2.0'})
    assert response.status_code == 200
    payload = response.json()
    assert set(fixture.keys()).issubset(payload.keys())
    assert payload['token_type'] == fixture['token_type']
    assert payload['license_status'] == fixture['license_status']
    assert payload['device_status'] == fixture['device_status']
    assert payload['user']['username'] == 'alice'


def test_login_invalid_credentials_uses_frozen_error_code() -> None:
    fixture = json.loads(LOGIN_ERROR_FIXTURE.read_text(encoding='utf-8'))
    client = get_client()
    response = client.post('/login', json={'username': 'alice', 'password': 'wrong', 'device_id': 'device_abc', 'client_version': '0.2.0'})
    assert response.status_code == 401
    payload = response.json()
    assert payload['error_code'] == fixture['error_code']
    assert payload['message'] == fixture['message']


def test_login_minimum_version_required_path() -> None:
    client = get_client()
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_abc', 'client_version': '0.1.0'})
    assert response.status_code == 403
    assert response.json()['error_code'] == 'minimum_version_required'


def test_login_non_semver_version_returns_minimum_version_required_instead_of_500() -> None:
    client = get_client()
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_abc', 'client_version': 'web-dev'})
    assert response.status_code == 403
    assert response.json()['error_code'] == 'minimum_version_required'


def test_login_disabled_and_revoked_paths() -> None:
    with session_scope() as session:
        user = session.query(User).filter_by(username='alice').one_or_none()
        if user is None:
            client = get_client()
            client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'seed-device', 'client_version': '0.2.0'})
            user = session.query(User).filter_by(username='alice').one()
        license_row = session.query(License).filter_by(user_id=user.id).one()
        license_row.license_status = 'disabled'
        session.commit()

    client = get_client()
    disabled = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_abc', 'client_version': '0.2.0'})
    assert disabled.status_code == 403
    assert disabled.json()['error_code'] == 'disabled'

    with session_scope() as session:
        user = session.query(User).filter_by(username='alice').one()
        license_row = session.query(License).filter_by(user_id=user.id).one()
        license_row.license_status = 'revoked'
        session.commit()

    revoked = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_abc', 'client_version': '0.2.0'})
    assert revoked.status_code == 403
    assert revoked.json()['error_code'] == 'revoked'


def test_login_response_shape_matches_openapi_required_fields() -> None:
    spec = yaml.safe_load(OPENAPI_PATH.read_text(encoding='utf-8'))
    required = spec['components']['schemas']['AuthSuccessResponse']['required']
    client = get_client()
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_abc', 'client_version': '0.2.0'})
    payload = response.json()
    for field in required:
        assert field in payload


def test_auth_core_migration_creates_expected_tables() -> None:
    with session_scope() as session:
        assert session.query(User).count() == 0
        assert session.query(Device).count() == 0
        assert session.query(EndUserSession).count() == 0
        assert session.query(RefreshToken).count() == 0
        assert session.query(AuditLog).count() == 0


def test_successful_login_creates_session_and_audit_rows() -> None:
    client = get_client()
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_abc', 'client_version': '0.2.0'}, headers={'X-Request-ID': 'req-123'})
    assert response.status_code == 200
    assert response.headers['X-Request-ID'] == 'req-123'
    assert response.headers['X-Trace-ID'] == 'req-123'
    with session_scope() as session:
        assert session.query(Device).count() == 1
        assert session.query(EndUserSession).count() == 1
        assert session.query(RefreshToken).count() == 1
        audit = session.query(AuditLog).one()
        assert audit.event_type == 'auth_login_succeeded'
        assert audit.request_id == 'req-123'


def test_login_rate_limit_blocks_after_threshold() -> None:
    client = get_client()
    for _ in range(5):
        response = client.post('/login', json={'username': 'alice', 'password': 'wrong', 'device_id': 'device_abc', 'client_version': '0.2.0'})
        assert response.status_code == 401
    blocked = client.post('/login', json={'username': 'alice', 'password': 'wrong', 'device_id': 'device_abc', 'client_version': '0.2.0'})
    assert blocked.status_code == 429
    assert blocked.json()['error_code'] == 'too_many_requests'


def test_semantic_version_comparison_keeps_0_10_above_0_2() -> None:
    client = get_client()
    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_abc', 'client_version': '0.10.0'})
    assert response.status_code == 200
