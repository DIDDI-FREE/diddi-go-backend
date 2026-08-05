"""ride_v3_safety_pricing_samples

Revision ID: d7e6f5a4c3b2
Revises: c4a2d8f1e9b7
Create Date: 2026-08-05
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "d7e6f5a4c3b2"
down_revision = "c4a2d8f1e9b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vehicles",
        sa.Column("comfort_level", sa.String(length=20), nullable=False, server_default="standard"),
        schema="ride",
    )
    op.add_column(
        "rides",
        sa.Column("comfort_level", sa.String(length=20), nullable=False, server_default="standard"),
        schema="ride",
    )
    op.add_column("rides", sa.Column("base_fare", sa.Numeric(10, 2), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("distance_fare", sa.Numeric(10, 2), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("duration_fare", sa.Numeric(10, 2), nullable=True), schema="ride")
    op.add_column(
        "rides",
        sa.Column("surge_multiplier", sa.Numeric(4, 2), nullable=False, server_default="1.00"),
        schema="ride",
    )
    op.add_column(
        "rides",
        sa.Column("surge_cap", sa.Numeric(4, 2), nullable=False, server_default="1.60"),
        schema="ride",
    )
    op.add_column(
        "rides",
        sa.Column("commission_rate", sa.Numeric(4, 2), nullable=False, server_default="0.08"),
        schema="ride",
    )
    op.add_column("rides", sa.Column("driver_payout_estimate", sa.Numeric(10, 2), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("platform_commission", sa.Numeric(10, 2), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("actual_distance_km", sa.Numeric(8, 3), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("actual_duration_seconds", sa.Integer(), nullable=True), schema="ride")
    op.add_column(
        "rides",
        sa.Column("payment_method", sa.String(length=20), nullable=False, server_default="cash"),
        schema="ride",
    )
    op.add_column("rides", sa.Column("share_token", sa.String(length=80), nullable=True), schema="ride")
    op.create_unique_constraint("uq_rides_share_token", "rides", ["share_token"], schema="ride")
    op.add_column("rides", sa.Column("share_expires_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("emergency_requested_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("emergency_status", sa.String(length=30), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("emergency_note", sa.Text(), nullable=True), schema="ride")
    op.add_column("ride_route_points", sa.Column("heading", sa.Integer(), nullable=True), schema="ride")
    op.add_column("ride_route_points", sa.Column("speed_kmh", sa.Numeric(7, 2), nullable=True), schema="ride")
    op.add_column("ride_route_points", sa.Column("accuracy_m", sa.Numeric(7, 2), nullable=True), schema="ride")
    op.add_column(
        "ride_route_points",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="driver"),
        schema="ride",
    )
    op.add_column("ride_route_points", sa.Column("metadata", postgresql.JSONB(), nullable=True), schema="ride")


def downgrade() -> None:
    op.drop_column("ride_route_points", "metadata", schema="ride")
    op.drop_column("ride_route_points", "source", schema="ride")
    op.drop_column("ride_route_points", "accuracy_m", schema="ride")
    op.drop_column("ride_route_points", "speed_kmh", schema="ride")
    op.drop_column("ride_route_points", "heading", schema="ride")
    op.drop_column("rides", "emergency_note", schema="ride")
    op.drop_column("rides", "emergency_status", schema="ride")
    op.drop_column("rides", "emergency_requested_at", schema="ride")
    op.drop_column("rides", "share_expires_at", schema="ride")
    op.drop_constraint("uq_rides_share_token", "rides", schema="ride", type_="unique")
    op.drop_column("rides", "share_token", schema="ride")
    op.drop_column("rides", "payment_method", schema="ride")
    op.drop_column("rides", "actual_duration_seconds", schema="ride")
    op.drop_column("rides", "actual_distance_km", schema="ride")
    op.drop_column("rides", "platform_commission", schema="ride")
    op.drop_column("rides", "driver_payout_estimate", schema="ride")
    op.drop_column("rides", "commission_rate", schema="ride")
    op.drop_column("rides", "surge_cap", schema="ride")
    op.drop_column("rides", "surge_multiplier", schema="ride")
    op.drop_column("rides", "duration_fare", schema="ride")
    op.drop_column("rides", "distance_fare", schema="ride")
    op.drop_column("rides", "base_fare", schema="ride")
    op.drop_column("rides", "comfort_level", schema="ride")
    op.drop_column("vehicles", "comfort_level", schema="ride")
