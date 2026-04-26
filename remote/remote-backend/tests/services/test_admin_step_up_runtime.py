from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.core.config import reset_settings_cache
from app.core.db import reset_db_state, session_scope
from app.core.security import hash_account_password
from app.migrations.alembic import ensure_database_on_head
from app.models import AdminStepUpGrant, AdminUser, Device, EndUserSession, License, User, UserDevice, UserEntitlement
from app.repositories.admin import AdminRepository
from app.schemas.admin import AdminLoginRequest, AdminStepUpVerifyRequest, AdminUserCreateRequest, AdminUserUpdateRequest
from app.services.admin_authz import (
    ADMIN_PERMISSION_DEVICES_WRITE,
    ADMIN_PERMISSION_USERS_WRITE,
)
from app.services.admin_service import AdminService, AdminServiceError, AdminServiceValidationError
from app.utils.time import utc_now_naive


@pytest.fixture
def migrated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    database_url = f"sqlite:///{(tmp_path / 'admin-step-up.sqlite3').as_posix()}"
    monkeypatch.setenv("REMOTE_BACKEND_DATABASE_URL", database_url)
    monkeypatch.setenv("REMOTE_BACKEND_APP_ENV", "test")
    reset_settings_cache()
    reset_db_state()
    ensure_database_on_head()
    yield database_url
    reset_db_state()
    reset_settings_cache()


def _seed_runtime_data() -> None:
    password_record = hash_account_password("admin-secret")
    now = utc_now_naive()
    with session_scope() as session:
        user = User(username="alice", display_name="Alice", email="alice@example.com", status="active", tenant_id="tenant_1")
        session.add(user)
        session.flush()
        session.add(License(user_id=user.id, license_status="active", expires_at=now + timedelta(days=30)))
        session.add(UserEntitlement(user_id=user.id, entitlement="dashboard:view", source="seed"))

        device = Device(device_id="device_1", status="bound", client_version="0.3.0")
        session.add(device)
        session.flush()
        session.add(UserDevice(user_id=user.id, device_id=device.id, binding_status="bound", bound_at=now, last_auth_at=now))
        session.add(
            EndUserSession(
                session_id="sess_1",
                user_id=user.id,
                device_id=device.id,
                auth_state="authenticated_active",
                access_token_hash="session_hash",
                expires_at=now + timedelta(hours=1),
                last_seen_at=now,
            )
        )
        session.add(
            AdminUser(
                username="admin",
                display_name="Remote Admin",
                password_hash=password_record.value,
                password_algo=password_record.algorithm,
                role="super_admin",
                status="active",
            )
        )
def test_verify_step_up_password_creates_grant(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")
        response = service.verify_step_up_password(
            login.access_token,
            AdminStepUpVerifyRequest(password="admin-secret", scope=ADMIN_PERMISSION_USERS_WRITE),
            client_ip="127.0.0.1",
        )

        assert response.scope == ADMIN_PERMISSION_USERS_WRITE
        assert response.method == "password"
        grant = session.query(AdminStepUpGrant).one()
        assert grant.scope == ADMIN_PERMISSION_USERS_WRITE
        assert grant.method == "password"
        assert grant.expires_at == response.expires_at
        assert grant.token_hash != response.step_up_token


def test_revoke_user_requires_step_up_token(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")

        with pytest.raises(AdminServiceError) as exc_info:
            service.revoke_user(login.access_token, "u_1")

    assert exc_info.value.error_code == "step_up_required"
    assert exc_info.value.status_code == 403


def test_revoke_user_succeeds_with_valid_step_up_token(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")
        step_up = service.verify_step_up_password(
            login.access_token,
            AdminStepUpVerifyRequest(password="admin-secret", scope=ADMIN_PERMISSION_USERS_WRITE),
            client_ip="127.0.0.1",
        )

        result = service.revoke_user(login.access_token, "u_1", step_up_token=step_up.step_up_token)

        assert result.success is True
        license_record = session.query(License).filter_by(user_id=1).one()
        assert license_record.license_status == "revoked"


def test_update_user_display_name_only_does_not_require_step_up(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")

        response = service.update_user(
            login.access_token,
            "u_1",
            AdminUserUpdateRequest(display_name="Alice Updated"),
        )

        assert response.display_name == "Alice Updated"


def test_update_user_sensitive_fields_require_step_up(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")

        with pytest.raises(AdminServiceError) as exc_info:
            service.update_user(
                login.access_token,
                "u_1",
                AdminUserUpdateRequest(entitlements=["dashboard:view", "publish:run"]),
            )

    assert exc_info.value.error_code == "step_up_required"
    assert exc_info.value.status_code == 403


def test_update_user_clearing_license_expiry_requires_step_up(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")

        with pytest.raises(AdminServiceError) as exc_info:
            service.update_user(
                login.access_token,
                "u_1",
                AdminUserUpdateRequest(license_expires_at=None),
            )

    assert exc_info.value.error_code == "step_up_required"
    assert exc_info.value.status_code == 403


def test_update_user_can_clear_license_expiry_with_valid_step_up_token(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")
        step_up = service.verify_step_up_password(
            login.access_token,
            AdminStepUpVerifyRequest(password="admin-secret", scope=ADMIN_PERMISSION_USERS_WRITE),
            client_ip="127.0.0.1",
        )

        response = service.update_user(
            login.access_token,
            "u_1",
            AdminUserUpdateRequest(license_expires_at=None),
            step_up_token=step_up.step_up_token,
        )

        license_record = session.query(License).filter_by(user_id=1).one()
        assert response.license_expires_at is None
        assert license_record.expires_at is None


def test_create_user_requires_step_up(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")

        with pytest.raises(AdminServiceError) as exc_info:
            service.create_user(
                login.access_token,
                AdminUserCreateRequest(
                    username="alice2",
                    password="TempSecret123!",
                    license_status="active",
                    entitlements=["dashboard:view"],
                ),
            )

    assert exc_info.value.error_code == "step_up_required"
    assert exc_info.value.status_code == 403


def test_create_user_succeeds_with_valid_step_up_token(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")
        step_up = service.verify_step_up_password(
            login.access_token,
            AdminStepUpVerifyRequest(password="admin-secret", scope=ADMIN_PERMISSION_USERS_WRITE),
            client_ip="127.0.0.1",
        )

        response = service.create_user(
            login.access_token,
            AdminUserCreateRequest(
                username="alice2",
                password="TempSecret123!",
                display_name="Alice 2",
                email="alice2@example.com",
                tenant_id="tenant_2",
                license_status="disabled",
                entitlements=["dashboard:view", "publish:run", "dashboard:view"],
            ),
            step_up_token=step_up.step_up_token,
        )

        created_user = session.query(User).filter_by(username="alice2").one()
        credential = created_user.credential
        license_record = created_user.license
        entitlements = sorted(row.entitlement for row in created_user.entitlements)

        assert response.id == f"u_{created_user.id}"
        assert response.username == "alice2"
        assert response.display_name == "Alice 2"
        assert response.status == "disabled"
        assert response.license_status == "disabled"
        assert credential is not None
        assert credential.password_hash != "TempSecret123!"
        assert credential.password_algo == "argon2id"
        assert license_record is not None
        assert license_record.license_status == "disabled"
        assert license_record.disabled_at is not None
        assert entitlements == ["dashboard:view", "publish:run"]


def test_create_user_duplicate_username_returns_validation_error(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")
        step_up = service.verify_step_up_password(
            login.access_token,
            AdminStepUpVerifyRequest(password="admin-secret", scope=ADMIN_PERMISSION_USERS_WRITE),
            client_ip="127.0.0.1",
        )

        with pytest.raises(AdminServiceValidationError) as exc_info:
            service.create_user(
                login.access_token,
                AdminUserCreateRequest(
                    username="alice",
                    password="TempSecret123!",
                    license_status="active",
                    entitlements=[],
                ),
                step_up_token=step_up.step_up_token,
            )

    assert exc_info.value.detail == [
        {
            "loc": ["body", "username"],
            "msg": "Username already exists.",
            "type": "value_error",
        }
    ]


def test_wrong_scope_step_up_token_is_rejected(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")
        step_up = service.verify_step_up_password(
            login.access_token,
            AdminStepUpVerifyRequest(password="admin-secret", scope=ADMIN_PERMISSION_DEVICES_WRITE),
            client_ip="127.0.0.1",
        )

        with pytest.raises(AdminServiceError) as exc_info:
            service.revoke_user(login.access_token, "u_1", step_up_token=step_up.step_up_token)

    assert exc_info.value.error_code == "step_up_invalid"
    assert exc_info.value.status_code == 403


def test_expired_step_up_token_is_rejected(migrated_database: str) -> None:
    _seed_runtime_data()

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        login = service.login(AdminLoginRequest(username="admin", password="admin-secret"), client_ip="127.0.0.1")
        step_up = service.verify_step_up_password(
            login.access_token,
            AdminStepUpVerifyRequest(password="admin-secret", scope=ADMIN_PERMISSION_USERS_WRITE),
            client_ip="127.0.0.1",
        )
        grant = session.query(AdminStepUpGrant).one()
        grant.expires_at = datetime(2020, 1, 1, 0, 0, 0)

        with pytest.raises(AdminServiceError) as exc_info:
            service.revoke_user(login.access_token, "u_1", step_up_token=step_up.step_up_token)

    assert exc_info.value.error_code == "step_up_expired"
    assert exc_info.value.status_code == 403
