from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
ALEMBIC_SCRIPT_LOCATION = PROJECT_ROOT / "migrations"
BASELINE_REVISION = "20260425_0001"
PRE_ALEMBIC_SCHEMA_MIGRATIONS_TABLE = "schema_migrations"
MANAGED_TABLES = {
    "admin_step_up_grants",
    "admin_sessions",
    "admin_users",
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


def _sqlite_connect_args(database_url: str) -> dict[str, bool]:
    return {"check_same_thread": False} if database_url.startswith("sqlite") else {}


def resolve_database_url(database_url: str | None = None) -> str:
    return database_url or get_settings().DATABASE_URL


def build_alembic_config(database_url: str | None = None) -> Config:
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(ALEMBIC_SCRIPT_LOCATION))
    config.set_main_option("sqlalchemy.url", resolve_database_url(database_url))
    return config


def get_current_revision(database_url: str | None = None) -> str | None:
    resolved_database_url = resolve_database_url(database_url)
    engine = create_engine(
        resolved_database_url,
        future=True,
        connect_args=_sqlite_connect_args(resolved_database_url),
    )
    try:
        with engine.connect() as connection:
            return MigrationContext.configure(connection).get_current_revision()
    finally:
        engine.dispose()


def get_head_revision(database_url: str | None = None) -> str:
    return ScriptDirectory.from_config(build_alembic_config(database_url)).get_current_head()


def has_untracked_schema_state(database_url: str | None = None) -> bool:
    resolved_database_url = resolve_database_url(database_url)
    engine = create_engine(
        resolved_database_url,
        future=True,
        connect_args=_sqlite_connect_args(resolved_database_url),
    )
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        return PRE_ALEMBIC_SCHEMA_MIGRATIONS_TABLE in table_names or bool(MANAGED_TABLES & table_names)
    finally:
        engine.dispose()


def upgrade_head(database_url: str | None = None) -> None:
    command.upgrade(build_alembic_config(database_url), "head")


def upgrade_to(revision: str, database_url: str | None = None) -> None:
    command.upgrade(build_alembic_config(database_url), revision)


def downgrade_to(revision: str, database_url: str | None = None) -> None:
    command.downgrade(build_alembic_config(database_url), revision)


def stamp_revision(revision: str, database_url: str | None = None) -> None:
    command.stamp(build_alembic_config(database_url), revision)


def ensure_database_on_head(database_url: str | None = None) -> None:
    resolved_database_url = resolve_database_url(database_url)
    current_revision = get_current_revision(resolved_database_url)
    if current_revision is None and has_untracked_schema_state(resolved_database_url):
        stamp_revision(BASELINE_REVISION, resolved_database_url)
    upgrade_head(resolved_database_url)
