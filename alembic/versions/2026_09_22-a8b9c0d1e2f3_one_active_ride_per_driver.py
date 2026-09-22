"""Prevent one driver from holding multiple active rides.

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-09-22 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8b9c0d1e2f3"
down_revision: str | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ACTIVE_DRIVER_STATUSES = "'matched', 'driver_en_route', 'in_progress', 'waiting'"


def upgrade() -> None:
    op.create_index(
        "uq_rides_one_active_per_driver",
        "rides",
        ["driver_id"],
        schema="ride",
        unique=True,
        postgresql_where=sa.text(
            f"driver_id IS NOT NULL AND status IN ({ACTIVE_DRIVER_STATUSES})",
        ),
    )


def downgrade() -> None:
    op.drop_index("uq_rides_one_active_per_driver", table_name="rides", schema="ride")
