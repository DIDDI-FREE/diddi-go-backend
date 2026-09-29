"""add driver profile photo file id

Revision ID: f4a5b6c7d8e9
Revises: e2f3a4b5c6d7
Create Date: 2026-09-29 02:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "f4a5b6c7d8e9"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("driver_profiles", sa.Column("profile_photo_file_id", sa.UUID(), nullable=True), schema="ride")


def downgrade() -> None:
    op.drop_column("driver_profiles", "profile_photo_file_id", schema="ride")
