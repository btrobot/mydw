from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

from app.core.config import reset_settings_cache
from app.core.db import reset_db_state, session_scope
from app.migrations.alembic import ensure_database_on_head, get_current_revision, get_head_revision
from app.models import AdminUser
from scripts import bootstrap_admin as bootstrap_admin_script
from scripts import migrate as migrate_script
from tests.migrations.support import seed_pre_alembic_schema


EXPECTED_TABLES = {
    "admin_sessions",
    "admin_users",
    "alembic_version",
    "audit_logs",
    "devices",
    "licenses",
    "refresh_tokens",
    "sessions",
    "user_credentials",
    "user_devices",
    "user_entitlements",
    "users",
}


def _assert_schema_tables(database_url: str) -> None:
    engine = create_engine(database_url, future=True)
    try:
        inspector = inspect(engine)
        assert EXPECTED_TABLES <= set(inspector.get_table_names())
    finally:
        engine.dispose()


def test_ensure_database_on_head_upgrades_empty_database(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'ensure-head-empty.sqlite3').as_posix()}"
    monkeypatch.setenv("REMOTE_BACKEND_DATABASE_URL", database_url)
    reset_settings_cache()
    reset_db_state()
    expected_head = get_head_revision(database_url)

    ensure_database_on_head()

    _assert_schema_tables(database_url)
    assert get_current_revision(database_url) == expected_head

    reset_db_state()
    reset_settings_cache()


def test_ensure_database_on_head_adopts_pre_alembic_database(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'ensure-head-pre-alembic.sqlite3').as_posix()}"
    monkeypatch.setenv("REMOTE_BACKEND_DATABASE_URL", database_url)
    reset_settings_cache()
    reset_db_state()
    seed_pre_alembic_schema(database_url)
    expected_head = get_head_revision(database_url)

    ensure_database_on_head()

    assert get_current_revision(database_url) == expected_head

    reset_db_state()
    reset_settings_cache()


def test_bootstrap_admin_migrate_uses_alembic_entrypoint(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'bootstrap-admin.sqlite3').as_posix()}"
    monkeypatch.setenv("REMOTE_BACKEND_DATABASE_URL", database_url)
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "admin-secret")
    expected_head = get_head_revision(database_url)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "bootstrap_admin.py",
            "--migrate",
            "--username",
            "admin",
            "--password-env",
            "BOOTSTRAP_ADMIN_PASSWORD",
            "--role",
            "super_admin",
            "--display-name",
            "Remote Admin",
        ],
    )
    reset_settings_cache()
    reset_db_state()

    assert bootstrap_admin_script.main() == 0

    assert get_current_revision(database_url) == expected_head
    with session_scope() as session:
        admin = session.query(AdminUser).filter_by(username="admin").one()
        assert admin.role == "super_admin"
        assert admin.display_name == "Remote Admin"
        assert admin.password_algo == "argon2id"

    reset_db_state()
    reset_settings_cache()


def test_migrate_script_current_reports_revision_after_upgrade(tmp_path: Path, monkeypatch, capsys) -> None:
    database_url = f"sqlite:///{(tmp_path / 'migrate-script.sqlite3').as_posix()}"
    monkeypatch.setenv("REMOTE_BACKEND_DATABASE_URL", database_url)
    reset_settings_cache()
    reset_db_state()
    expected_head = get_head_revision(database_url)

    monkeypatch.setattr(sys, "argv", ["migrate.py", "ensure-head"])
    assert migrate_script.main() == 0

    monkeypatch.setattr(sys, "argv", ["migrate.py", "current"])
    assert migrate_script.main() == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == expected_head

    reset_db_state()
    reset_settings_cache()
