from __future__ import annotations

from datetime import timedelta
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
from app.models import AuditLog, Device, EndUserSession, License, User
from app.repositories.auth import AuthRepository
from app.services.control_service import DeviceControlService, SessionControlService, UserControlService


@pytest.fixture(autouse=True)
def isolated_remote_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / 'remote_pr21.sqlite3'
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


def login_success(client: TestClient, *, device_id: str = 'device_pr21', client_version: str = '0.2.0') -> dict:
    response = client.post(
        '/login',
        json={'username': 'alice', 'password': 'secret', 'device_id': device_id, 'client_version': client_version},
    )
    assert response.status_code == 200
    return response.json()


def user_id_for(username: str = 'alice') -> int:
    with session_scope() as session:
        user = session.query(User).filter_by(username=username).one()
        return user.id


def control_services(session):
    repository = AuthRepository(session)
    session_control = SessionControlService(repository)
    return (
        UserControlService(repository, session_control),
        DeviceControlService(repository, session_control),
    )


def test_revoke_user_forces_login_refresh_and_me_to_revoked() -> None:
    client = get_client()
    login_payload = login_success(client)
    user_id = user_id_for()

    with session_scope() as session:
        user_control, _ = control_services(session)
        user_control.revoke_user(user_id, actor_type='admin', actor_id='admin_1')

    relogin = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_pr21', 'client_version': '0.2.0'})
    assert relogin.status_code == 403
    assert relogin.json()['error_code'] == 'revoked'

    refresh = client.post('/refresh', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_pr21', 'client_version': '0.2.0'})
    assert refresh.status_code == 403
    assert refresh.json()['error_code'] == 'revoked'

    me = client.get('/me', headers={'Authorization': f"Bearer {login_payload['access_token']}"})
    assert me.status_code == 403
    assert me.json()['error_code'] == 'revoked'

    with session_scope() as session:
        audit_events = [row.event_type for row in session.query(AuditLog).order_by(AuditLog.id.asc()).all()]
        assert 'authorization_user_revoked' in audit_events


def test_restore_user_reenables_login_after_revoke() -> None:
    client = get_client()
    login_success(client)
    user_id = user_id_for()

    with session_scope() as session:
        user_control, _ = control_services(session)
        user_control.revoke_user(user_id, actor_type='admin', actor_id='admin_1')
        user_control.restore_user(user_id, actor_type='admin', actor_id='admin_1')

    restored = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_pr21', 'client_version': '0.2.0'})
    assert restored.status_code == 200


def test_disable_user_forces_disabled_without_revoking_existing_session() -> None:
    client = get_client()
    login_payload = login_success(client)
    user_id = user_id_for()

    with session_scope() as session:
        user_control, _ = control_services(session)
        user_control.disable_user(user_id, actor_type='admin', actor_id='admin_1')

    refresh = client.post('/refresh', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_pr21', 'client_version': '0.2.0'})
    assert refresh.status_code == 403
    assert refresh.json()['error_code'] == 'disabled'

    me = client.get('/me', headers={'Authorization': f"Bearer {login_payload['access_token']}"})
    assert me.status_code == 403
    assert me.json()['error_code'] == 'disabled'

    with session_scope() as session:
        session_row = session.query(EndUserSession).one()
        assert session_row.revoked_at is None
        assert session_row.auth_state == 'authorization_disabled'


def test_device_unbind_forces_device_mismatch_on_refresh_and_me() -> None:
    client = get_client()
    login_payload = login_success(client)
    user_id = user_id_for()

    with session_scope() as session:
        _, device_control = control_services(session)
        device_control.unbind_device(user_id, 'device_pr21', actor_type='admin', actor_id='admin_1')

    refresh = client.post('/refresh', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_pr21', 'client_version': '0.2.0'})
    assert refresh.status_code == 403
    assert refresh.json()['error_code'] == 'device_mismatch'

    me = client.get('/me', headers={'Authorization': f"Bearer {login_payload['access_token']}"})
    assert me.status_code == 403
    assert me.json()['error_code'] == 'device_mismatch'

    with session_scope() as session:
        device = session.query(Device).filter_by(device_id='device_pr21').one()
        assert device.status == 'unbound'


def test_device_disable_forces_device_mismatch_until_rebound() -> None:
    client = get_client()
    login_payload = login_success(client)
    user_id = user_id_for()

    with session_scope() as session:
        _, device_control = control_services(session)
        device_control.disable_device('device_pr21', actor_type='admin', actor_id='admin_1')

    refresh = client.post('/refresh', json={'refresh_token': login_payload['refresh_token'], 'device_id': 'device_pr21', 'client_version': '0.2.0'})
    assert refresh.status_code == 403
    assert refresh.json()['error_code'] == 'device_mismatch'

    with session_scope() as session:
        _, device_control = control_services(session)
        device_control.rebind_device(user_id, 'device_pr21', actor_type='admin', actor_id='admin_1')

    relogin = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_pr21', 'client_version': '0.2.0'})
    assert relogin.status_code == 200


def test_minimum_supported_version_policy_is_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('REMOTE_BACKEND_MINIMUM_SUPPORTED_VERSION', '0.5.0')
    reset_settings_cache()
    client = get_client()

    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_pr21', 'client_version': '0.2.0'})
    assert response.status_code == 403
    assert response.json()['error_code'] == 'minimum_version_required'
    assert response.json()['details']['minimum_supported_version'] == '0.5.0'

    reset_settings_cache()


def test_offline_grace_policy_uses_default_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('REMOTE_BACKEND_DEFAULT_OFFLINE_GRACE_HOURS', '72')
    reset_settings_cache()
    client = get_client()
    login_success(client)

    with session_scope() as session:
        user = session.query(User).filter_by(username='alice').one()
        license_row = session.query(License).filter_by(user_id=user.id).one()
        license_row.offline_grace_hours = None
        expires_at = license_row.expires_at

    response = client.post('/login', json={'username': 'alice', 'password': 'secret', 'device_id': 'device_pr21', 'client_version': '0.2.0'})
    assert response.status_code == 200
    offline_grace_until = response.json()['offline_grace_until']
    assert offline_grace_until is not None

    expected = (expires_at + timedelta(hours=72)).isoformat()
    assert offline_grace_until.startswith(expected[:16])

    reset_settings_cache()


def test_me_uses_minimum_version_fallback_when_device_version_is_missing() -> None:
    client = get_client()
    login_payload = login_success(client)

    with session_scope() as session:
        device = session.query(Device).filter_by(device_id='device_pr21').one()
        device.client_version = None

    response = client.get('/me', headers={'Authorization': f"Bearer {login_payload['access_token']}"})
    assert response.status_code == 200
    assert response.json()['minimum_supported_version'] == '0.2.0'
