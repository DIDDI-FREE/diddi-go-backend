"""Add persistent quotes and frozen MVP departure fields.

Revision ID: 5c6d7e8f9a0b
Revises: 4b5c6d7e8f9a
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5c6d7e8f9a0b"
down_revision: str | None = "4b5c6d7e8f9a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("uq_rides_one_active_per_driver", table_name="rides", schema="ride")
    op.create_index(
        "uq_rides_one_active_per_driver",
        "rides",
        ["driver_id"],
        unique=True,
        schema="ride",
        postgresql_where=sa.text(
            "driver_id IS NOT NULL AND status IN ('matched', 'driver_en_route', 'arrived', 'in_progress', 'waiting')"
        ),
    )
    op.create_table(
        "ride_quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("passenger_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("auth.users.id"), nullable=False),
        sa.Column("pickup_lat", sa.Numeric(9, 6), nullable=False),
        sa.Column("pickup_lng", sa.Numeric(9, 6), nullable=False),
        sa.Column("pickup_address", sa.Text(), nullable=True),
        sa.Column("dropoff_lat", sa.Numeric(9, 6), nullable=False),
        sa.Column("dropoff_lng", sa.Numeric(9, 6), nullable=False),
        sa.Column("dropoff_address", sa.Text(), nullable=True),
        sa.Column("vehicle_category", sa.String(20), nullable=False),
        sa.Column("comfort_level", sa.String(20), nullable=False),
        sa.Column("estimated_fare", sa.Numeric(10, 2), nullable=False),
        sa.Column("distance_km", sa.Numeric(8, 3), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("base_fare", sa.Numeric(10, 2), nullable=False),
        sa.Column("distance_fare", sa.Numeric(10, 2), nullable=False),
        sa.Column("duration_fare", sa.Numeric(10, 2), nullable=False),
        sa.Column("surge_multiplier", sa.Numeric(4, 2), nullable=False),
        sa.Column("surge_cap", sa.Numeric(4, 2), nullable=False),
        sa.Column("commission_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("platform_commission", sa.Numeric(10, 2), nullable=False),
        sa.Column("driver_payout_estimate", sa.Numeric(10, 2), nullable=False),
        sa.Column("tariff_version", sa.String(80), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ride_id", postgresql.UUID(as_uuid=True), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="ride",
    )
    op.create_index("ix_ride_quotes_expires_at", "ride_quotes", ["expires_at"], schema="ride")
    op.create_index(
        "ix_ride_quotes_passenger_expires",
        "ride_quotes",
        ["passenger_user_id", "expires_at"],
        schema="ride",
    )
    op.add_column("rides", sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True), schema="ride")
    op.create_unique_constraint("uq_rides_quote_id", "rides", ["quote_id"], schema="ride")

    op.add_column("rides", sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("pre_ride_wait_started_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("pre_ride_wait_seconds", sa.Integer(), nullable=False, server_default="0"), schema="ride")
    op.add_column("rides", sa.Column("pre_ride_wait_fee", sa.Numeric(10, 2), nullable=False, server_default="0"), schema="ride")
    op.add_column("rides", sa.Column("start_code_hash", sa.String(64), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("start_code_attempts", sa.Integer(), nullable=False, server_default="0"), schema="ride")
    op.add_column("rides", sa.Column("start_code_blocked_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("start_code_used_at", sa.DateTime(timezone=True), nullable=True), schema="ride")

    op.add_column("vehicles", sa.Column("vehicle_plate_photo_file_id", postgresql.UUID(as_uuid=True), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_plate_photo_url", sa.Text(), nullable=True), schema="ride")
    op.create_table(
        "ride_emergency_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ride_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ride.rides.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_role", sa.String(30), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("contact_notified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notification_results", postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint("ride_id", "sequence", name="uq_ride_emergency_event_sequence"),
        schema="ride",
    )
    op.create_index(
        "ix_ride_emergency_events_ride_requested",
        "ride_emergency_events",
        ["ride_id", "requested_at"],
        schema="ride",
    )


def downgrade() -> None:
    op.drop_index("ix_ride_emergency_events_ride_requested", table_name="ride_emergency_events", schema="ride")
    op.drop_table("ride_emergency_events", schema="ride")
    op.drop_index("uq_rides_one_active_per_driver", table_name="rides", schema="ride")
    op.create_index(
        "uq_rides_one_active_per_driver",
        "rides",
        ["driver_id"],
        unique=True,
        schema="ride",
        postgresql_where=sa.text(
            "driver_id IS NOT NULL AND status IN ('matched', 'driver_en_route', 'in_progress', 'waiting')"
        ),
    )
    op.drop_column("vehicles", "vehicle_plate_photo_url", schema="ride")
    op.drop_column("vehicles", "vehicle_plate_photo_file_id", schema="ride")
    for column in (
        "start_code_used_at",
        "start_code_blocked_at",
        "start_code_attempts",
        "start_code_hash",
        "pre_ride_wait_fee",
        "pre_ride_wait_seconds",
        "pre_ride_wait_started_at",
        "arrived_at",
    ):
        op.drop_column("rides", column, schema="ride")
    op.drop_constraint("uq_rides_quote_id", "rides", schema="ride", type_="unique")
    op.drop_column("rides", "quote_id", schema="ride")
    op.drop_index("ix_ride_quotes_passenger_expires", table_name="ride_quotes", schema="ride")
    op.drop_index("ix_ride_quotes_expires_at", table_name="ride_quotes", schema="ride")
    op.drop_table("ride_quotes", schema="ride")
