from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

VERSION = '0002_add_access_token_hash'


def upgrade(connection: Connection) -> None:
    inspector = inspect(connection)
    session_columns = {column['name'] for column in inspector.get_columns('sessions')}
    if 'access_token_hash' not in session_columns:
        connection.execute(text('ALTER TABLE sessions ADD COLUMN access_token_hash TEXT'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS ix_sessions_access_token_hash ON sessions (access_token_hash)'))


def downgrade(connection: Connection) -> None:
    # SQLite cannot safely drop columns in-place. The base migration teardown
    # removes the full table during test downgrades, so this step is a no-op.
    return None
