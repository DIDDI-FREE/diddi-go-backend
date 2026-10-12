"""Persist the provider-agnostic payout destination on driver withdrawals.

Revision ID: 7e8f9a0b1c2d
Revises: 6d7e8f9a0b1c
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7e8f9a0b1c2d"
down_revision: str | None = "6d7e8f9a0b1c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "driver_withdrawals",
        sa.Column("beneficiary_destination", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="payment",
    )


def downgrade() -> None:
    op.drop_column("driver_withdrawals", "beneficiary_destination", schema="payment")
