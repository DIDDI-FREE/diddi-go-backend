"""driver wallets and ledger

Revision ID: f1c2d3e4a5b6
Revises: a4c9e2d8f6b1
Create Date: 2026-08-28 23:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f1c2d3e4a5b6"
down_revision = "a4c9e2d8f6b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "driver_wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("driver_id", name="uq_payment_driver_wallets_driver_id"),
        schema="payment",
    )
    op.create_index(
        op.f("ix_payment_driver_wallets_driver_id"),
        "driver_wallets",
        ["driver_id"],
        unique=False,
        schema="payment",
    )

    op.create_table(
        "driver_ledger_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("direction", sa.String(length=12), nullable=False),
        sa.Column("entry_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reference_type", sa.String(length=40), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "driver_id",
            "entry_type",
            "reference_type",
            "reference_id",
            name="uq_payment_driver_ledger_reference",
        ),
        schema="payment",
    )
    op.create_index(
        "idx_payment_driver_ledger_driver_created",
        "driver_ledger_entries",
        ["driver_id", "created_at"],
        unique=False,
        schema="payment",
    )

    op.create_table(
        "driver_topups",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payment_intent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("business_reference", sa.String(length=128), nullable=True),
        sa.Column("idempotency_key", sa.String(length=160), nullable=True),
        sa.Column("provider_status", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_intent_id", name="uq_payment_driver_topups_payment_intent_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_payment_driver_topups_idempotency_key"),
        schema="payment",
    )
    op.create_index(
        "idx_payment_driver_topups_driver_created",
        "driver_topups",
        ["driver_id", "created_at"],
        unique=False,
        schema="payment",
    )


def downgrade() -> None:
    op.drop_index("idx_payment_driver_topups_driver_created", table_name="driver_topups", schema="payment")
    op.drop_table("driver_topups", schema="payment")
    op.drop_index("idx_payment_driver_ledger_driver_created", table_name="driver_ledger_entries", schema="payment")
    op.drop_table("driver_ledger_entries", schema="payment")
    op.drop_index(op.f("ix_payment_driver_wallets_driver_id"), table_name="driver_wallets", schema="payment")
    op.drop_table("driver_wallets", schema="payment")
