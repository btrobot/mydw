"""
Step 1 / PR1 baseline tests for local auth config, model, and migration foundation.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import settings
from models import RemoteAuthSession


def test_remote_auth_config_exposes_foundation_defaults() -> None:
    assert settings.REMOTE_AUTH_BASE_URL == ""
    assert settings.REMOTE_AUTH_TIMEOUT == 15
    assert settings.REMOTE_AUTH_DEFAULT_OFFLINE_GRACE_HOURS == 24
    assert settings.REMOTE_AUTH_ENCRYPT_KEY
    assert settings.REMOTE_AUTH_DEVICE_ID_PATH == "data/remote_auth_device.json"


def test_remote_auth_session_model_persists_only_non_secret_fields() -> None:
    columns = set(RemoteAuthSession.__table__.columns.keys())

    assert columns >= {
        "id",
        "auth_state",
        "remote_user_id",
        "display_name",
        "license_status",
        "entitlements_snapshot",
        "expires_at",
        "last_verified_at",
        "offline_grace_until",
        "denial_reason",
        "device_id",
        "created_at",
        "updated_at",
    }

    assert "refresh_token" not in columns
    assert "access_token" not in columns


@pytest.mark.asyncio
async def test_remote_auth_migration_creates_table_and_indexes(tmp_path: Path) -> None:
    db_path = tmp_path / "remote_auth_foundation.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)

    try:
        migration_module = __import__(
            "migrations.023_remote_auth_sessions",
            fromlist=["run_migration"],
        )
        await migration_module.run_migration(engine)

        async with engine.connect() as conn:
            tables = await conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='remote_auth_sessions'"
            )
            assert tables.fetchone() is not None

            columns = await conn.exec_driver_sql("PRAGMA table_info(remote_auth_sessions)")
            column_names = {row[1] for row in columns.fetchall()}

            assert column_names >= {
                "id",
                "auth_state",
                "remote_user_id",
                "display_name",
                "license_status",
                "entitlements_snapshot",
                "expires_at",
                "last_verified_at",
                "offline_grace_until",
                "denial_reason",
                "device_id",
                "created_at",
                "updated_at",
            }
            assert "refresh_token" not in column_names
            assert "access_token" not in column_names

            indexes = await conn.exec_driver_sql("PRAGMA index_list(remote_auth_sessions)")
            index_names = {row[1] for row in indexes.fetchall()}
            assert "ix_remote_auth_sessions_auth_state" in index_names
            assert "ix_remote_auth_sessions_remote_user_id" in index_names
            assert "ix_remote_auth_sessions_license_status" in index_names
            assert "ix_remote_auth_sessions_device_id" in index_names
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_remote_auth_migration_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "remote_auth_foundation_idempotent.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)

    try:
        migration_module = __import__(
            "migrations.023_remote_auth_sessions",
            fromlist=["run_migration"],
        )
        await migration_module.run_migration(engine)
        await migration_module.run_migration(engine)

        async with engine.connect() as conn:
            count = await conn.exec_driver_sql(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='remote_auth_sessions'"
            )
            assert count.fetchone()[0] == 1
    finally:
        await engine.dispose()
