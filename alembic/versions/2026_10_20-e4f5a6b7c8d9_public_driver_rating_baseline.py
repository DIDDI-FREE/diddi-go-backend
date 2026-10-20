"""Restore the public 5.00 rating baseline for new drivers.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-10-20
"""

from alembic import op
import sqlalchemy as sa


revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE ride.driver_profiles SET rating_avg = 5.00 WHERE rating_avg IS NULL")
    op.alter_column(
        "driver_profiles",
        "rating_avg",
        existing_type=sa.Numeric(precision=3, scale=2),
        nullable=False,
        server_default=sa.text("5.00"),
        schema="ride",
    )


def downgrade() -> None:
    op.alter_column(
        "driver_profiles",
        "rating_avg",
        existing_type=sa.Numeric(precision=3, scale=2),
        nullable=True,
        server_default=None,
        schema="ride",
    )
