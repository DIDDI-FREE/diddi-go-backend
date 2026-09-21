"""Add manual ride waiting state accounting.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-09-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e6f7a8b9c0d1"
down_revision: str | None = "d5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("rides", sa.Column("waiting_started_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column(
        "rides",
        sa.Column("waiting_duration_seconds", sa.Integer(), server_default="0", nullable=False),
        schema="ride",
    )
    op.add_column(
        "rides",
        sa.Column("waiting_fee", sa.Numeric(10, 2), server_default="0", nullable=False),
        schema="ride",
    )
    op.add_column(
        "rides",
        sa.Column("waiting_rate_per_minute", sa.Numeric(10, 2), nullable=True),
        schema="ride",
    )


def downgrade() -> None:
    op.drop_column("rides", "waiting_rate_per_minute", schema="ride")
    op.drop_column("rides", "waiting_fee", schema="ride")
    op.drop_column("rides", "waiting_duration_seconds", schema="ride")
    op.drop_column("rides", "waiting_started_at", schema="ride")
