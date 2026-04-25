"""Add password_algo tracking for admin users.

Revision ID: 20260425_0002
Revises: 20260425_0001
Create Date: 2026-04-25 22:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260425_0002"
down_revision = "20260425_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("admin_users") as batch_op:
        batch_op.add_column(sa.Column("password_algo", sa.String(length=32), nullable=True))

    op.execute(sa.text("UPDATE admin_users SET password_algo = 'pbkdf2_sha256' WHERE password_algo IS NULL"))

    with op.batch_alter_table("admin_users") as batch_op:
        batch_op.alter_column(
            "password_algo",
            existing_type=sa.String(length=32),
            nullable=False,
            server_default="pbkdf2_sha256",
        )
        batch_op.alter_column(
            "password_algo",
            existing_type=sa.String(length=32),
            server_default=None,
        )


def downgrade() -> None:
    with op.batch_alter_table("admin_users") as batch_op:
        batch_op.drop_column("password_algo")
