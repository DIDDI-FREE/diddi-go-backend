"""add driver withdrawal quotes and payouts

Revision ID: 6d7e8f9a0b1c
Revises: 5c6d7e8f9a0b
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "6d7e8f9a0b1c"
down_revision: str | None = "5c6d7e8f9a0b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "driver_withdrawal_quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("fees", sa.Numeric(12, 2), nullable=False),
        sa.Column("net_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="XOF"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount > 0 AND fees >= 0 AND net_amount > 0", name="ck_driver_withdrawal_quote_amounts"),
        schema="payment",
    )
    op.create_index(
        "idx_payment_withdrawal_quotes_driver",
        "driver_withdrawal_quotes",
        ["driver_id", "created_at"],
        schema="payment",
    )
    op.create_table(
        "driver_withdrawals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("fees", sa.Numeric(12, 2), nullable=False),
        sa.Column("net_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="XOF"),
        sa.Column("beneficiary_reference", sa.String(128), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("payout_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("business_reference", sa.String(128), nullable=False),
        sa.Column("idempotency_key", sa.String(160), nullable=False),
        sa.Column("provider_status", sa.String(40), nullable=True),
        sa.Column("failure_code", sa.String(80), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reserved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("succeeded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("amount > 0 AND fees >= 0 AND net_amount > 0", name="ck_driver_withdrawal_amounts"),
        sa.CheckConstraint(
            "status IN ('reserved','processing','succeeded','failed','released')",
            name="ck_driver_withdrawal_status",
        ),
        sa.UniqueConstraint("quote_id", name="uq_payment_driver_withdrawals_quote"),
        sa.UniqueConstraint("payout_id", name="uq_payment_driver_withdrawals_payout"),
        sa.UniqueConstraint("idempotency_key", name="uq_payment_driver_withdrawals_idempotency"),
        schema="payment",
    )
    op.create_index(
        "idx_payment_driver_withdrawals_driver_created",
        "driver_withdrawals",
        ["driver_id", "created_at"],
        schema="payment",
    )
    op.create_index(
        "idx_payment_driver_withdrawals_status_updated",
        "driver_withdrawals",
        ["status", "updated_at"],
        schema="payment",
    )


def downgrade() -> None:
    op.drop_table("driver_withdrawals", schema="payment")
    op.drop_table("driver_withdrawal_quotes", schema="payment")
