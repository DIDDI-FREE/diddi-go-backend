"""Isolate Google Play Review accounts from production actors.

Revision ID: a1b2c3d4e5f6
Revises: 0a1b2c3d4e5f
Create Date: 2026-11-02
"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "0a1b2c3d4e5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_review_account", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="auth",
    )
    op.add_column(
        "driver_profiles",
        sa.Column("is_review_account", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="ride",
    )
    op.add_column(
        "rides",
        sa.Column("is_review_account", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="ride",
    )
    op.create_index("ix_rides_review_status", "rides", ["is_review_account", "status"], schema="ride")


def downgrade() -> None:
    op.drop_index("ix_rides_review_status", table_name="rides", schema="ride")
    op.drop_column("rides", "is_review_account", schema="ride")
    op.drop_column("driver_profiles", "is_review_account", schema="ride")
    op.drop_column("users", "is_review_account", schema="auth")
