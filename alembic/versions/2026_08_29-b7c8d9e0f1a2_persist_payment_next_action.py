"""persist payment next action

Revision ID: b7c8d9e0f1a2
Revises: f1c2d3e4a5b6
Create Date: 2026-08-29 12:55:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "b7c8d9e0f1a2"
down_revision = "f1c2d3e4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("provider_next_action", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="payment",
    )
    op.add_column(
        "driver_topups",
        sa.Column("provider_next_action", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="payment",
    )
    # Reconciliation walks non-terminal intents by age; without these the job
    # degrades into a full scan of every payment ever made.
    op.create_index(
        "idx_payment_transactions_status_created",
        "transactions",
        ["status", "created_at"],
        schema="payment",
    )
    op.create_index(
        "idx_payment_driver_topups_status_created",
        "driver_topups",
        ["status", "created_at"],
        schema="payment",
    )


def downgrade() -> None:
    op.drop_index("idx_payment_driver_topups_status_created", table_name="driver_topups", schema="payment")
    op.drop_index("idx_payment_transactions_status_created", table_name="transactions", schema="payment")
    op.drop_column("driver_topups", "provider_next_action", schema="payment")
    op.drop_column("transactions", "provider_next_action", schema="payment")
