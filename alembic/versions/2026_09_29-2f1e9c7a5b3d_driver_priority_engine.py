"""driver priority engine — ledger + dispatch config (SCRUM-63 Phase 3)

Revision ID: 2f1e9c7a5b3d
Revises: f4a5b6c7d8e9
Create Date: 2026-09-29 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "2f1e9c7a5b3d"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "driver_priority_events",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column(
            "driver_id", sa.UUID(),
            sa.ForeignKey("ride.driver_profiles.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("ride_id", sa.UUID(), nullable=True),
        sa.Column("zone_id", sa.UUID(), nullable=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        schema="ride",
    )
    op.create_index(
        "idx_driver_priority_events_driver_created",
        "driver_priority_events",
        ["driver_id", "created_at"],
        schema="ride",
    )

    op.create_table(
        "dispatch_config",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("search_radius_km", sa.Numeric(6, 2), nullable=False),
        sa.Column("search_radius_step_km", sa.Numeric(6, 2), nullable=False),
        sa.Column("search_radius_max_km", sa.Numeric(6, 2), nullable=False),
        sa.Column("offer_wave_size", sa.Integer(), nullable=False),
        sa.Column("search_budget_seconds", sa.Integer(), nullable=False),
        sa.Column("eta_shortlist_size", sa.Integer(), nullable=False),
        sa.Column("priority_window_days", sa.Integer(), nullable=False),
        sa.Column("priority_cap_seconds", sa.Integer(), nullable=False),
        sa.Column("priority_seconds_per_point", sa.Integer(), nullable=False),
        sa.Column("points_ride_completed", sa.Integer(), nullable=False),
        sa.Column("points_ride_cancelled_by_driver", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="ride",
    )
    # Seed the single effective row with the settings defaults so the engine
    # has config before an operator ever edits it.
    op.execute(
        """
        INSERT INTO ride.dispatch_config (
            search_radius_km, search_radius_step_km, search_radius_max_km,
            offer_wave_size, search_budget_seconds, eta_shortlist_size,
            priority_window_days, priority_cap_seconds, priority_seconds_per_point,
            points_ride_completed, points_ride_cancelled_by_driver
        ) VALUES (5.0, 2.0, 15.0, 5, 120, 10, 7, 120, 10, 1, -3)
        """,
    )


def downgrade() -> None:
    op.drop_table("dispatch_config", schema="ride")
    op.drop_index("idx_driver_priority_events_driver_created", table_name="driver_priority_events", schema="ride")
    op.drop_table("driver_priority_events", schema="ride")
