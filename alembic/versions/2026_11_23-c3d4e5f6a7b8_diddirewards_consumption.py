"""Persist the Rewards consumption reference on rides."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rides", sa.Column("rewards_consumption_id", sa.UUID(), nullable=True), schema="ride")
    op.create_table(
        "rewards_event_outbox",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(length=160), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("ride_id", sa.UUID(), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
        schema="payment",
    )
    op.create_index("idx_payment_rewards_outbox_due", "rewards_event_outbox", ["status", "next_attempt_at"], schema="payment")
    op.create_index("ix_payment_rewards_event_outbox_ride_id", "rewards_event_outbox", ["ride_id"], schema="payment")


def downgrade() -> None:
    op.drop_index("ix_payment_rewards_event_outbox_ride_id", table_name="rewards_event_outbox", schema="payment")
    op.drop_index("idx_payment_rewards_outbox_due", table_name="rewards_event_outbox", schema="payment")
    op.drop_table("rewards_event_outbox", schema="payment")
    op.drop_column("rides", "rewards_consumption_id", schema="ride")
