"""notification_devices

Revision ID: 9df1b0a7c6c3
Revises: c554cac77c8c
Create Date: 2026-08-03 00:00:00.000000+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9df1b0a7c6c3"
down_revision: str | None = "c554cac77c8c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS notification")
    op.create_table(
        "user_devices",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("push_provider", sa.String(length=20), nullable=False),
        sa.Column("push_token", sa.Text(), nullable=False),
        sa.Column("device_id", sa.String(length=120), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("push_token", name="user_devices_push_token_unique"),
        schema="notification",
    )
    op.create_index(
        op.f("ix_notification_user_devices_user_id"),
        "user_devices",
        ["user_id"],
        unique=False,
        schema="notification",
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_notification_user_devices_user_id"), table_name="user_devices", schema="notification")
    op.drop_table("user_devices", schema="notification")
    op.execute("DROP SCHEMA IF EXISTS notification")
