"""driver_kyc_fields

Revision ID: b3f6c2a9d8e1
Revises: 9df1b0a7c6c3
Create Date: 2026-08-04
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "b3f6c2a9d8e1"
down_revision = "9df1b0a7c6c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("driver_profiles", sa.Column("legal_name", sa.String(length=160), nullable=True), schema="ride")
    op.add_column("driver_profiles", sa.Column("birth_date", sa.Date(), nullable=True), schema="ride")
    op.add_column("driver_profiles", sa.Column("residence_address", sa.Text(), nullable=True), schema="ride")
    op.add_column("driver_profiles", sa.Column("license_document_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("driver_profiles", sa.Column("national_id_document_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("driver_profiles", sa.Column("selfie_document_url", sa.Text(), nullable=True), schema="ride")
    op.add_column(
        "driver_profiles",
        sa.Column("kyc_submitted_at", sa.DateTime(timezone=True), nullable=True),
        schema="ride",
    )
    op.add_column(
        "driver_profiles",
        sa.Column("kyc_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        schema="ride",
    )
    op.add_column("driver_profiles", sa.Column("kyc_review_notes", sa.Text(), nullable=True), schema="ride")


def downgrade() -> None:
    op.drop_column("driver_profiles", "kyc_review_notes", schema="ride")
    op.drop_column("driver_profiles", "kyc_reviewed_at", schema="ride")
    op.drop_column("driver_profiles", "kyc_submitted_at", schema="ride")
    op.drop_column("driver_profiles", "selfie_document_url", schema="ride")
    op.drop_column("driver_profiles", "national_id_document_url", schema="ride")
    op.drop_column("driver_profiles", "license_document_url", schema="ride")
    op.drop_column("driver_profiles", "residence_address", schema="ride")
    op.drop_column("driver_profiles", "birth_date", schema="ride")
    op.drop_column("driver_profiles", "legal_name", schema="ride")
