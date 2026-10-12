"""Add idempotency receipts for durable GPS sample batches.

Revision ID: 8f9a0b1c2d3e
Revises: 7e8f9a0b1c2d
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8f9a0b1c2d3e"
down_revision: str | None = "7e8f9a0b1c2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ride_location_batches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "ride_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ride.rides.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("samples_count", sa.Integer(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("ride_id", "batch_id", name="uq_ride_location_batch"),
        schema="ride",
    )
    op.create_index(
        "ix_ride_location_batches_ride_created",
        "ride_location_batches",
        ["ride_id", "created_at"],
        schema="ride",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ride_location_batches_ride_created",
        table_name="ride_location_batches",
        schema="ride",
    )
    op.drop_table("ride_location_batches", schema="ride")
