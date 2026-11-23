"""Persist DiddiRewards context on quotes and rides."""

from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    ride_columns = (
        ("rewards_campaign_id", sa.String(120)),
        ("rewards_entitlement_id", sa.UUID()),
        ("rewards_campaign_version_id", sa.UUID()),
        ("rewards_discount_amount", sa.Numeric(10, 2)),
        ("rewards_reservation_id", sa.UUID()),
        ("rewards_status", sa.String(30)),
    )
    quote_columns = (
        ("rewards_campaign_id", sa.String(120)),
        ("rewards_entitlement_id", sa.UUID()),
        ("rewards_campaign_version_id", sa.UUID()),
        ("rewards_discount_amount", sa.Numeric(10, 2)),
        ("rewards_final_amount", sa.Numeric(10, 2)),
        ("rewards_reason", sa.String(120)),
    )
    for name, column_type in ride_columns:
        op.add_column("rides", sa.Column(name, column_type, nullable=True), schema="ride")
    for name, column_type in quote_columns:
        op.add_column("ride_quotes", sa.Column(name, column_type, nullable=True), schema="ride")


def downgrade() -> None:
    for name, _ in (
        ("rewards_reason", None),
        ("rewards_final_amount", None),
        ("rewards_discount_amount", None),
        ("rewards_campaign_version_id", None),
        ("rewards_entitlement_id", None),
        ("rewards_campaign_id", None),
    ):
        op.drop_column("ride_quotes", name, schema="ride")
    for name, _ in (
        ("rewards_status", None),
        ("rewards_reservation_id", None),
        ("rewards_discount_amount", None),
        ("rewards_campaign_version_id", None),
        ("rewards_entitlement_id", None),
        ("rewards_campaign_id", None),
    ):
        op.drop_column("rides", name, schema="ride")
