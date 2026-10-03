"""Persist ride service type and add Pilotage temporal indexes.

Revision ID: 3a4b5c6d7e8f
Revises: 2f1e9c7a5b3d
Create Date: 2026-10-03
"""

import sqlalchemy as sa
from alembic import op

revision = "3a4b5c6d7e8f"
down_revision = "2f1e9c7a5b3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rides",
        sa.Column("vehicle_category", sa.String(length=20), server_default="standard", nullable=False),
        schema="ride",
    )
    op.execute(
        """
        UPDATE ride.rides AS r
        SET vehicle_category = v.category
        FROM ride.vehicles AS v
        WHERE r.vehicle_id = v.id
        """
    )
    op.create_index("ix_rides_requested_at", "rides", ["requested_at"], schema="ride")
    op.create_index("ix_rides_completed_at", "rides", ["completed_at"], schema="ride")


def downgrade() -> None:
    op.drop_index("ix_rides_completed_at", table_name="rides", schema="ride")
    op.drop_index("ix_rides_requested_at", table_name="rides", schema="ride")
    op.drop_column("rides", "vehicle_category", schema="ride")
