"""Persist unpaid completed-ride debts for passenger eligibility.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "passenger_debts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("passenger_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ride_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="XOF"),
        sa.Column("status", sa.String(40), nullable=False, server_default="open"),
        sa.Column("reason", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settled_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint("ride_id", name="uq_payment_passenger_debts_ride_id"),
        sa.CheckConstraint("amount > 0", name="passenger_debts_amount_positive"),
        sa.CheckConstraint(
            "status IN ('open', 'mobile_money_pending', 'cash_pending_confirmation', 'settled')",
            name="passenger_debts_status_check",
        ),
        schema="payment",
    )
    op.create_index(
        "idx_payment_passenger_debts_open", "passenger_debts", ["passenger_user_id", "status"], schema="payment"
    )


def downgrade() -> None:
    op.drop_index("idx_payment_passenger_debts_open", table_name="passenger_debts", schema="payment")
    op.drop_table("passenger_debts", schema="payment")
