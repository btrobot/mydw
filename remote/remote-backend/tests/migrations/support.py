from __future__ import annotations

from alembic import command
from sqlalchemy import create_engine, text

from app.migrations.alembic import build_alembic_config


PRE_ALEMBIC_SCHEMA_VERSIONS = (
    "0001_initial_auth_core",
    "0002_add_access_token_hash",
    "0003_add_admin_auth",
)


def seed_pre_alembic_schema(database_url: str) -> None:
    command.upgrade(build_alembic_config(database_url), "20260425_0001")

    engine = create_engine(database_url, future=True)
    try:
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
            connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)"))
            for version in PRE_ALEMBIC_SCHEMA_VERSIONS:
                connection.execute(
                    text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                    {"version": version},
                )
    finally:
        engine.dispose()
