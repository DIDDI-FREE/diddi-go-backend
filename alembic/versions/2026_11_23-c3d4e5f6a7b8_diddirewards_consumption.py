"""Persist the Rewards consumption reference on rides."""

from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rides", sa.Column("rewards_consumption_id", sa.UUID(), nullable=True), schema="ride")


def downgrade() -> None:
    op.drop_column("rides", "rewards_consumption_id", schema="ride")
