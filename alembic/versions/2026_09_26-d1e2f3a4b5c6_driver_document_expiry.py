"""Add driver KYC document expiry dates (SCRUM-524 #3).

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-09-26 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "c0d1e2f3a4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "driver_profiles",
        sa.Column("license_expires_at", sa.DateTime(timezone=True), nullable=True),
        schema="ride",
    )
    op.add_column(
        "driver_profiles",
        sa.Column("national_id_expires_at", sa.DateTime(timezone=True), nullable=True),
        schema="ride",
    )


def downgrade() -> None:
    op.drop_column("driver_profiles", "national_id_expires_at", schema="ride")
    op.drop_column("driver_profiles", "license_expires_at", schema="ride")
