from __future__ import annotations

from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, inspect

from app.core.config import reset_settings_cache
from app.core.db import reset_db_state
from app.migrations.alembic import build_alembic_config, get_current_revision, get_head_revision
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


def test_alembic_upgrade_head_creates_current_schema(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'alembic-upgrade.sqlite3').as_posix()}"
    config = build_alembic_config(database_url)
    expected_head = get_head_revision(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url, future=True)
    try:
        inspector = inspect(engine)
        assert EXPECTED_TABLES <= set(inspector.get_table_names())
        admin_user_columns = {column["name"] for column in inspector.get_columns("admin_users")}
        assert "password_algo" in admin_user_columns
    finally:
        engine.dispose()

    assert get_current_revision(database_url) == expected_head


def test_alembic_downgrade_base_clears_revision_state(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'alembic-downgrade.sqlite3').as_posix()}"
    config = build_alembic_config(database_url)

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    engine = create_engine(database_url, future=True)
    try:
        inspector = inspect(engine)
        remaining_tables = set(inspector.get_table_names())
        assert "users" not in inspector.get_table_names()
        assert remaining_tables <= {"alembic_version"}
    finally:
        engine.dispose()

    assert get_current_revision(database_url) is None


def test_alembic_stamp_adopts_existing_pre_alembic_schema(tmp_path: Path, monkeypatch) -> None:
    database_url = f"sqlite:///{(tmp_path / 'pre-alembic.sqlite3').as_posix()}"
    config = build_alembic_config(database_url)

    monkeypatch.setenv("REMOTE_BACKEND_DATABASE_URL", database_url)
    reset_settings_cache()
    reset_db_state()
    seed_pre_alembic_schema(database_url)

    command.stamp(config, "20260425_0001")

    assert get_current_revision(database_url) == "20260425_0001"

    reset_db_state()
    reset_settings_cache()
