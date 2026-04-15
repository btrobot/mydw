from __future__ import annotations

from sqlalchemy.engine import Connection

from app.models import Base

VERSION = '0001_initial_auth_core'


def upgrade(connection: Connection) -> None:
    Base.metadata.create_all(bind=connection)


def downgrade(connection: Connection) -> None:
    Base.metadata.drop_all(bind=connection)
