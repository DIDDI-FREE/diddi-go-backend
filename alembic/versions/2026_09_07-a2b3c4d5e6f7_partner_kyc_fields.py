"""add partner KYC fields

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-09-07 11:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "a2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("partners", sa.Column("registration_document_file_id", sa.UUID(), nullable=True), schema="partner")
    op.add_column("partners", sa.Column("tax_document_file_id", sa.UUID(), nullable=True), schema="partner")
    op.add_column(
        "partners",
        sa.Column("representative_id_document_file_id", sa.UUID(), nullable=True),
        schema="partner",
    )
    op.add_column(
        "partners",
        sa.Column("fleet_ownership_document_file_id", sa.UUID(), nullable=True),
        schema="partner",
    )
    op.add_column("partners", sa.Column("registration_document_url", sa.String(length=1000), nullable=True), schema="partner")
    op.add_column("partners", sa.Column("tax_document_url", sa.String(length=1000), nullable=True), schema="partner")
    op.add_column(
        "partners",
        sa.Column("representative_id_document_url", sa.String(length=1000), nullable=True),
        schema="partner",
    )
    op.add_column(
        "partners",
        sa.Column("fleet_ownership_document_url", sa.String(length=1000), nullable=True),
        schema="partner",
    )
    op.add_column("partners", sa.Column("kyc_submitted_at", sa.DateTime(timezone=True), nullable=True), schema="partner")
    op.add_column("partners", sa.Column("kyc_reviewed_at", sa.DateTime(timezone=True), nullable=True), schema="partner")
    op.add_column("partners", sa.Column("kyc_review_notes", sa.String(length=1000), nullable=True), schema="partner")


def downgrade() -> None:
    op.drop_column("partners", "kyc_review_notes", schema="partner")
    op.drop_column("partners", "kyc_reviewed_at", schema="partner")
    op.drop_column("partners", "kyc_submitted_at", schema="partner")
    op.drop_column("partners", "fleet_ownership_document_url", schema="partner")
    op.drop_column("partners", "representative_id_document_url", schema="partner")
    op.drop_column("partners", "tax_document_url", schema="partner")
    op.drop_column("partners", "registration_document_url", schema="partner")
    op.drop_column("partners", "fleet_ownership_document_file_id", schema="partner")
    op.drop_column("partners", "representative_id_document_file_id", schema="partner")
    op.drop_column("partners", "tax_document_file_id", schema="partner")
    op.drop_column("partners", "registration_document_file_id", schema="partner")
