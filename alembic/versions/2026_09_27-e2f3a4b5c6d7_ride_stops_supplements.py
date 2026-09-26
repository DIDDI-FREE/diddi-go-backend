"""Add ride stops and fare supplements (SCRUM-524 #2, manual pricing).

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-09-27 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e2f3a4b5c6d7"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "rides",
        sa.Column(
            "supplements_total",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
        schema="ride",
    )
    op.create_table(
        "ride_stops",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            primary_key=True, server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("ride_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["ride_id"], ["ride.rides.id"], ondelete="CASCADE"),
        schema="ride",
    )
    op.create_index("ix_ride_stops_ride_id", "ride_stops", ["ride_id"], schema="ride")
    op.create_table(
        "ride_supplements",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            primary_key=True, server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("ride_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("reason", sa.String(120), nullable=False),
        sa.Column("source", sa.String(10), nullable=False, server_default="manual"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["ride_id"], ["ride.rides.id"], ondelete="CASCADE"),
        sa.CheckConstraint("amount > 0", name="ride_supplements_amount_positive"),
        schema="ride",
    )
    op.create_index(
        "ix_ride_supplements_ride_id", "ride_supplements", ["ride_id"], schema="ride"
    )


def downgrade() -> None:
    op.drop_index("ix_ride_supplements_ride_id", table_name="ride_supplements", schema="ride")
    op.drop_table("ride_supplements", schema="ride")
    op.drop_index("ix_ride_stops_ride_id", table_name="ride_stops", schema="ride")
    op.drop_table("ride_stops", schema="ride")
    op.drop_column("rides", "supplements_total", schema="ride")
