"""Normalize ride payments to the public mobile_money method.

Revision ID: a0b1c2d3e4f5
Revises: 9a0b1c2d3e4f
"""

from alembic import op
import sqlalchemy as sa

revision = "a0b1c2d3e4f5"
down_revision = "9a0b1c2d3e4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rides", sa.Column("completion_reason", sa.String(40), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("early_stop_requested_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("early_stop_expires_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("early_stop_requested_by_user_id", sa.Uuid(), nullable=True), schema="ride")
    op.add_column("rides", sa.Column("early_stop_confirmed_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.execute(
        "UPDATE ride.rides SET payment_method = 'mobile_money' "
        "WHERE payment_method IN ('wave', 'diddipay')",
    )
    op.execute(
        "UPDATE payment.transactions SET method = 'mobile_money' "
        "WHERE method IN ('wave', 'diddipay')",
    )


def downgrade() -> None:
    op.execute(
        "UPDATE ride.rides SET payment_method = 'diddipay' "
        "WHERE payment_method = 'mobile_money'",
    )
    op.drop_column("rides", "early_stop_confirmed_at", schema="ride")
    op.drop_column("rides", "early_stop_requested_by_user_id", schema="ride")
    op.drop_column("rides", "early_stop_expires_at", schema="ride")
    op.drop_column("rides", "early_stop_requested_at", schema="ride")
    op.drop_column("rides", "completion_reason", schema="ride")
    op.execute(
        "UPDATE payment.transactions SET method = 'diddipay' "
        "WHERE method = 'mobile_money'",
    )
