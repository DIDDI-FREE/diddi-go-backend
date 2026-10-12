"""Add passenger decisions to ride supplements.

Revision ID: 9a0b1c2d3e4f
Revises: 8f9a0b1c2d3e
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9a0b1c2d3e4f"
down_revision: str | None = "8f9a0b1c2d3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ride_supplements",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="accepted"),
        schema="ride",
    )
    op.add_column(
        "ride_supplements",
        sa.Column("decided_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        schema="ride",
    )
    op.add_column(
        "ride_supplements",
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        schema="ride",
    )
    op.create_check_constraint(
        "ride_supplements_status_valid",
        "ride_supplements",
        "status IN ('pending', 'accepted', 'disputed')",
        schema="ride",
    )
    # Existing rows were already included in supplements_total and therefore
    # remain accepted. New rows use the application-side `pending` default.
    op.alter_column("ride_supplements", "status", server_default=None, schema="ride")


def downgrade() -> None:
    op.drop_constraint(
        "ride_supplements_status_valid",
        "ride_supplements",
        schema="ride",
        type_="check",
    )
    op.drop_column("ride_supplements", "decided_at", schema="ride")
    op.drop_column("ride_supplements", "decided_by_user_id", schema="ride")
    op.drop_column("ride_supplements", "status", schema="ride")
