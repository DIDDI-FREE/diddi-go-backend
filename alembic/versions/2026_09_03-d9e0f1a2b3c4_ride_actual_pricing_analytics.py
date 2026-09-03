"""persist actual ride pricing analytics

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-09-03 16:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "d9e0f1a2b3c4"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rides", sa.Column("actual_pricing_fare", sa.Numeric(10, 2), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("pricing_delta", sa.Numeric(10, 2), nullable=True), schema="ride")


def downgrade() -> None:
    op.drop_column("rides", "pricing_delta", schema="ride")
    op.drop_column("rides", "actual_pricing_fare", schema="ride")
