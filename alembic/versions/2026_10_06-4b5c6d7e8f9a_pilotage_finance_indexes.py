"""Add indexes used by the Pilotage financial summary.

Revision ID: 4b5c6d7e8f9a
Revises: 3a4b5c6d7e8f
Create Date: 2026-10-06
"""

from alembic import op

revision = "4b5c6d7e8f9a"
down_revision = "3a4b5c6d7e8f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_driver_topups_created_at", "driver_topups", ["created_at"], schema="payment")
    op.create_index("ix_driver_topups_paid_at", "driver_topups", ["paid_at"], schema="payment")
    op.create_index("ix_payment_transactions_ride_status", "transactions", ["ride_id", "status"], schema="payment")


def downgrade() -> None:
    op.drop_index("ix_payment_transactions_ride_status", table_name="transactions", schema="payment", if_exists=True)
    op.drop_index("ix_driver_topups_paid_at", table_name="driver_topups", schema="payment", if_exists=True)
    op.drop_index("ix_driver_topups_created_at", table_name="driver_topups", schema="payment", if_exists=True)
