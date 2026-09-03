"""persist DiddiMap ride trace id

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-09-03 10:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rides", sa.Column("map_trace_id", sa.String(length=64), nullable=True), schema="ride")
    op.create_index("idx_ride_rides_map_trace_id", "rides", ["map_trace_id"], schema="ride")


def downgrade() -> None:
    op.drop_index("idx_ride_rides_map_trace_id", table_name="rides", schema="ride")
    op.drop_column("rides", "map_trace_id", schema="ride")
