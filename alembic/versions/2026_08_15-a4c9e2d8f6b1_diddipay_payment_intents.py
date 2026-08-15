"""diddipay_payment_intents

Revision ID: a4c9e2d8f6b1
Revises: d7e6f5a4c3b2
Create Date: 2026-08-15 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a4c9e2d8f6b1"
down_revision: str | Sequence[str] | None = "d7e6f5a4c3b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("payment_intent_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="payment",
    )
    op.add_column("transactions", sa.Column("business_reference", sa.String(length=128), nullable=True), schema="payment")
    op.add_column("transactions", sa.Column("idempotency_key", sa.String(length=160), nullable=True), schema="payment")
    op.add_column("transactions", sa.Column("provider_status", sa.String(length=40), nullable=True), schema="payment")
    op.add_column(
        "transactions",
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        schema="payment",
    )
    op.create_unique_constraint(
        "uq_payment_transactions_payment_intent_id",
        "transactions",
        ["payment_intent_id"],
        schema="payment",
    )
    op.create_unique_constraint(
        "uq_payment_transactions_idempotency_key",
        "transactions",
        ["idempotency_key"],
        schema="payment",
    )
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("payment_intent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("business_reference", sa.String(length=128), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="payment",
    )
    op.create_index(
        op.f("ix_payment_webhook_events_payment_intent_id"),
        "webhook_events",
        ["payment_intent_id"],
        unique=False,
        schema="payment",
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_webhook_events_payment_intent_id"), table_name="webhook_events", schema="payment")
    op.drop_table("webhook_events", schema="payment")
    op.drop_constraint("uq_payment_transactions_idempotency_key", "transactions", schema="payment", type_="unique")
    op.drop_constraint(
        "uq_payment_transactions_payment_intent_id",
        "transactions",
        schema="payment",
        type_="unique",
    )
    op.drop_column("transactions", "paid_at", schema="payment")
    op.drop_column("transactions", "provider_status", schema="payment")
    op.drop_column("transactions", "idempotency_key", schema="payment")
    op.drop_column("transactions", "business_reference", schema="payment")
    op.drop_column("transactions", "payment_intent_id", schema="payment")
