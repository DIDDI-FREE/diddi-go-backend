"""add driver KYC back document fields

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-09-04 09:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("driver_profiles", sa.Column("license_back_document_file_id", sa.UUID(), nullable=True), schema="ride")
    op.add_column(
        "driver_profiles",
        sa.Column("national_id_back_document_file_id", sa.UUID(), nullable=True),
        schema="ride",
    )
    op.add_column("driver_profiles", sa.Column("license_back_document_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("driver_profiles", sa.Column("national_id_back_document_url", sa.Text(), nullable=True), schema="ride")


def downgrade() -> None:
    op.drop_column("driver_profiles", "national_id_back_document_url", schema="ride")
    op.drop_column("driver_profiles", "license_back_document_url", schema="ride")
    op.drop_column("driver_profiles", "national_id_back_document_file_id", schema="ride")
    op.drop_column("driver_profiles", "license_back_document_file_id", schema="ride")
