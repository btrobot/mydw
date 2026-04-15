from __future__ import annotations

from sqlalchemy import text

from app.core.db import get_engine
from .versions import (
    migration_0001_initial_auth_core,
    migration_0002_add_access_token_hash,
    migration_0003_add_admin_auth,
)

MIGRATIONS = [
    migration_0001_initial_auth_core,
    migration_0002_add_access_token_hash,
    migration_0003_add_admin_auth,
]


def upgrade() -> None:
    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)'))
        for migration in MIGRATIONS:
            existing = connection.execute(text('SELECT version FROM schema_migrations WHERE version = :version'), {'version': migration.VERSION}).fetchone()
            if existing is None:
                migration.upgrade(connection)
                connection.execute(text('INSERT INTO schema_migrations (version) VALUES (:version)'), {'version': migration.VERSION})


def downgrade() -> None:
    engine = get_engine()
    with engine.begin() as connection:
        for migration in reversed(MIGRATIONS):
            existing = connection.execute(text('SELECT version FROM schema_migrations WHERE version = :version'), {'version': migration.VERSION}).fetchone()
            if existing is not None:
                migration.downgrade(connection)
                connection.execute(text('DELETE FROM schema_migrations WHERE version = :version'), {'version': migration.VERSION})
