from __future__ import annotations

from sqlalchemy.engine import Connection

from app.models import AdminSession, AdminUser

VERSION = '0003_add_admin_auth'


def upgrade(connection: Connection) -> None:
    AdminUser.__table__.create(bind=connection, checkfirst=True)
    AdminSession.__table__.create(bind=connection, checkfirst=True)


def downgrade(connection: Connection) -> None:
    AdminSession.__table__.drop(bind=connection, checkfirst=True)
    AdminUser.__table__.drop(bind=connection, checkfirst=True)
