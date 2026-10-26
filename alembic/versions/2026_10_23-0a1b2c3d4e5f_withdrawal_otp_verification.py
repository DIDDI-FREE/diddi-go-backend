"""Add payout-specific OTP challenges for driver withdrawals.

Revision ID: 0a1b2c3d4e5f
Revises: f5a6b7c8d9e0
Create Date: 2026-10-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0a1b2c3d4e5f"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "driver_withdrawal_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("beneficiary_destination", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recipient_phone", sa.String(length=16), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        schema="payment",
    )
    op.create_index(
        "idx_payment_withdrawal_verifications_driver_created",
        "driver_withdrawal_verifications",
        ["driver_id", "created_at"],
        schema="payment",
    )


def downgrade() -> None:
    op.drop_index(
        "idx_payment_withdrawal_verifications_driver_created",
        table_name="driver_withdrawal_verifications",
        schema="payment",
    )
    op.drop_table("driver_withdrawal_verifications", schema="payment")
