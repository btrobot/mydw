from __future__ import annotations

from datetime import datetime, timedelta
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
from app.models import AdminSession, AdminUser, AuditLog

OPENAPI_PATH = ROOT / 'remote' / 'remote-shared' / 'openapi' / 'remote-auth-v1.yaml'


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / 'remote_pr13.sqlite3'
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


def admin_login(client: TestClient, *, password: str = 'admin-secret') -> dict:
    response = client.post('/admin/login', json={'username': 'admin', 'password': password}, headers={'X-Request-ID': 'req-admin-login'})
    assert response.status_code == 200
    return response.json()


def test_admin_login_success_creates_independent_session_and_audit() -> None:
    client = get_client()
    response = client.post('/admin/login', json={'username': 'admin', 'password': 'admin-secret'}, headers={'X-Request-ID': 'req-admin-login'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['user']['username'] == 'admin'
    assert payload['user']['role'] == 'super_admin'
    assert payload['token_type'] == 'Bearer'
    assert response.headers['X-Request-ID'] == 'req-admin-login'
    assert response.headers['X-Trace-ID'] == 'req-admin-login'

    with session_scope() as session:
        assert session.query(AdminUser).count() >= 1
        admin_session = session.query(AdminSession).one()
        assert admin_session.session_id == payload['session_id']
        audit = session.query(AuditLog).order_by(AuditLog.id.asc()).all()
        assert any(item.event_type == 'admin_login_succeeded' for item in audit)


def test_admin_login_invalid_credentials_and_rate_limit() -> None:
    client = get_client()
    for _ in range(5):
        response = client.post('/admin/login', json={'username': 'admin', 'password': 'wrong'})
        assert response.status_code == 401
        assert response.json()['error_code'] == 'invalid_credentials'
    blocked = client.post('/admin/login', json={'username': 'admin', 'password': 'wrong'})
    assert blocked.status_code == 429
    assert blocked.json()['error_code'] == 'too_many_requests'


def test_admin_login_does_not_auto_seed_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('REMOTE_BACKEND_APP_ENV', 'production')
    reset_settings_cache()
    admin_login_rate_limiter.reset()

    client = get_client()
    response = client.post('/admin/login', json={'username': 'admin', 'password': 'admin-secret'})
    assert response.status_code == 401
    assert response.json()['error_code'] == 'invalid_credentials'

    with session_scope() as session:
        assert session.query(AdminUser).count() == 0

    reset_settings_cache()


def test_admin_session_requires_independent_admin_token() -> None:
    client = get_client()
    admin_payload = admin_login(client)
    session_response = client.get('/admin/session', headers={'Authorization': f"Bearer {admin_payload['access_token']}", 'X-Request-ID': 'req-admin-session'})
    assert session_response.status_code == 200
    assert session_response.json()['session_id'] == admin_payload['session_id']
    assert session_response.json()['user']['username'] == 'admin'
    assert session_response.headers['X-Request-ID'] == 'req-admin-session'

    user_login = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_abc', 'client_version': '0.2.0'})
    assert user_login.status_code == 200
    wrong_domain = client.get('/admin/session', headers={'Authorization': f"Bearer {user_login.json()['access_token']}"})
    assert wrong_domain.status_code == 401
    assert wrong_domain.json()['error_code'] == 'token_expired'


def test_admin_session_rejects_expired_or_disabled_admin() -> None:
    client = get_client()
    admin_payload = admin_login(client)

    with session_scope() as session:
        admin_session = session.query(AdminSession).one()
        admin_session.expires_at = datetime.utcnow() - timedelta(seconds=1)

    expired = client.get('/admin/session', headers={'Authorization': f"Bearer {admin_payload['access_token']}"})
    assert expired.status_code == 401
    assert expired.json()['error_code'] == 'token_expired'

    admin_payload = admin_login(client)
    with session_scope() as session:
        admin_user = session.query(AdminUser).filter_by(username='admin').one()
        admin_user.status = 'disabled'

    disabled = client.get('/admin/session', headers={'Authorization': f"Bearer {admin_payload['access_token']}"})
    assert disabled.status_code == 403
    assert disabled.json()['error_code'] == 'forbidden'


def test_admin_openapi_contains_auth_endpoints_and_required_fields() -> None:
    spec = yaml.safe_load(OPENAPI_PATH.read_text(encoding='utf-8'))
    assert '/admin/login' in spec['paths']
    assert '/admin/session' in spec['paths']

    login_required = spec['components']['schemas']['AdminLoginResponse']['required']
    session_required = spec['components']['schemas']['AdminCurrentSessionResponse']['required']
    client = get_client()
    login_payload = admin_login(client)

    for field in login_required:
        assert field in login_payload

    session_payload = client.get('/admin/session', headers={'Authorization': f"Bearer {login_payload['access_token']}"}).json()
    for field in session_required:
        assert field in session_payload


def test_admin_cors_allows_direct_open_shell_origin() -> None:
    client = get_client()
    response = client.options(
        '/admin/login',
        headers={
            'Origin': 'null',
            'Access-Control-Request-Method': 'POST',
        },
    )
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'null'
