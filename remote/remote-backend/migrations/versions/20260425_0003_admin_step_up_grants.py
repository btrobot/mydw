"""Add admin step-up grants for destructive actions.

Revision ID: 20260425_0003
Revises: 20260425_0002
Create Date: 2026-04-26 12:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260425_0003"
down_revision = "20260425_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_step_up_grants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_session_id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["admin_session_id"], ["admin_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_step_up_grants_admin_session_id"), "admin_step_up_grants", ["admin_session_id"], unique=False)
    op.create_index(op.f("ix_admin_step_up_grants_expires_at"), "admin_step_up_grants", ["expires_at"], unique=False)
    op.create_index(op.f("ix_admin_step_up_grants_scope"), "admin_step_up_grants", ["scope"], unique=False)
    op.create_index(op.f("ix_admin_step_up_grants_token_hash"), "admin_step_up_grants", ["token_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_step_up_grants_token_hash"), table_name="admin_step_up_grants")
    op.drop_index(op.f("ix_admin_step_up_grants_scope"), table_name="admin_step_up_grants")
    op.drop_index(op.f("ix_admin_step_up_grants_expires_at"), table_name="admin_step_up_grants")
    op.drop_index(op.f("ix_admin_step_up_grants_admin_session_id"), table_name="admin_step_up_grants")
    op.drop_table("admin_step_up_grants")
