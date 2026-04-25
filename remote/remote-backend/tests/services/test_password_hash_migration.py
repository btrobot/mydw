from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import reset_settings_cache
from app.core.db import reset_db_state, session_scope
from app.core.security import PASSWORD_ALGO_ARGON2ID, PASSWORD_ALGO_PBKDF2_SHA256, hash_account_password
from app.migrations.alembic import ensure_database_on_head
from app.models import AdminUser, License, User, UserCredential
from app.repositories.admin import AdminRepository
from app.repositories.auth import AuthRepository
from app.schemas.admin import AdminLoginRequest
from app.schemas.auth import LoginRequest
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from scripts.bootstrap_admin import bootstrap_admin


@pytest.fixture
def migrated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    database_url = f"sqlite:///{(tmp_path / 'password-migration.sqlite3').as_posix()}"
    monkeypatch.setenv("REMOTE_BACKEND_DATABASE_URL", database_url)
    monkeypatch.setenv("REMOTE_BACKEND_APP_ENV", "test")
    monkeypatch.setenv("REMOTE_BACKEND_PASSWORD_HASH_DEFAULT_ALGO", PASSWORD_ALGO_ARGON2ID)
    reset_settings_cache()
    reset_db_state()
    ensure_database_on_head()
    yield database_url
    reset_db_state()
    reset_settings_cache()


def _legacy_password_record(monkeypatch: pytest.MonkeyPatch, password: str):
    monkeypatch.setenv("REMOTE_BACKEND_PASSWORD_HASH_DEFAULT_ALGO", PASSWORD_ALGO_PBKDF2_SHA256)
    reset_settings_cache()
    record = hash_account_password(password)
    monkeypatch.setenv("REMOTE_BACKEND_PASSWORD_HASH_DEFAULT_ALGO", PASSWORD_ALGO_ARGON2ID)
    reset_settings_cache()
    return record


def test_auth_service_login_rehashes_legacy_pbkdf2_password_to_argon2(
    migrated_database: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_record = _legacy_password_record(monkeypatch, "secret")

    with session_scope() as session:
        user = User(username="alice", display_name="Alice", status="active", tenant_id="tenant_1")
        session.add(user)
        session.flush()
        session.add(
            UserCredential(
                user_id=user.id,
                password_hash=legacy_record.value,
                password_algo=legacy_record.algorithm,
            )
        )
        session.add(License(user_id=user.id, license_status="active"))

    with session_scope() as session:
        service = AuthService(AuthRepository(session))
        response = service.login(
            LoginRequest(
                username="alice",
                password="secret",
                device_id="device_1",
                client_version="0.2.0",
            ),
            client_ip="127.0.0.1",
        )
        assert response.user.username == "alice"

    with session_scope() as session:
        credential = session.query(UserCredential).join(User).filter(User.username == "alice").one()
        assert credential.password_algo == PASSWORD_ALGO_ARGON2ID
        assert credential.password_hash.startswith("$argon2id$")


def test_admin_service_login_rehashes_legacy_pbkdf2_password_to_argon2(
    migrated_database: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_record = _legacy_password_record(monkeypatch, "admin-secret")

    with session_scope() as session:
        session.add(
            AdminUser(
                username="admin",
                display_name="Remote Admin",
                password_hash=legacy_record.value,
                password_algo=legacy_record.algorithm,
                role="super_admin",
                status="active",
            )
        )

    with session_scope() as session:
        service = AdminService(AdminRepository(session))
        response = service.login(
            AdminLoginRequest(username="admin", password="admin-secret"),
            client_ip="127.0.0.1",
        )
        assert response.user.username == "admin"

    with session_scope() as session:
        admin_user = session.query(AdminUser).filter_by(username="admin").one()
        assert admin_user.password_algo == PASSWORD_ALGO_ARGON2ID
        assert admin_user.password_hash.startswith("$argon2id$")


def test_auth_service_login_survives_password_rehash_failure(
    migrated_database: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy_record = _legacy_password_record(monkeypatch, "secret")

    with session_scope() as session:
        user = User(username="legacy-user", display_name="Legacy User", status="active", tenant_id="tenant_1")
        session.add(user)
        session.flush()
        session.add(
            UserCredential(
                user_id=user.id,
                password_hash=legacy_record.value,
                password_algo=legacy_record.algorithm,
            )
        )
        session.add(License(user_id=user.id, license_status="active"))

    monkeypatch.setattr("app.services.auth_service.hash_account_password", lambda password: (_ for _ in ()).throw(RuntimeError("boom")))

    with session_scope() as session:
        service = AuthService(AuthRepository(session))
        response = service.login(
            LoginRequest(
                username="legacy-user",
                password="secret",
                device_id="device_2",
                client_version="0.2.0",
            ),
            client_ip="127.0.0.1",
        )
        assert response.user.username == "legacy-user"

    with session_scope() as session:
        credential = session.query(UserCredential).join(User).filter(User.username == "legacy-user").one()
        assert credential.password_algo == PASSWORD_ALGO_PBKDF2_SHA256
        assert credential.password_hash == legacy_record.value


def test_seed_and_bootstrap_password_writes_use_argon2(
    migrated_database: str,
) -> None:
    with session_scope() as session:
        AuthService(AuthRepository(session)).ensure_seed_user()

    bootstrap_admin(
        username="bootstrap-admin",
        password="bootstrap-secret",
        role="super_admin",
        display_name="Bootstrap Admin",
        status="active",
    )

    with session_scope() as session:
        seed_credential = session.query(UserCredential).join(User).filter(User.username == "alice").one()
        bootstrap_user = session.query(AdminUser).filter_by(username="bootstrap-admin").one()
        assert seed_credential.password_algo == PASSWORD_ALGO_ARGON2ID
        assert seed_credential.password_hash.startswith("$argon2id$")
        assert bootstrap_user.password_algo == PASSWORD_ALGO_ARGON2ID
        assert bootstrap_user.password_hash.startswith("$argon2id$")
