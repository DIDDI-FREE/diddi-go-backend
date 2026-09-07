"""add vehicle KYV fields

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-09-07 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "b3c4d5e6f7a8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vehicles", sa.Column("insurance_document_file_id", sa.UUID(), nullable=True), schema="ride")
    op.add_column(
        "vehicles",
        sa.Column("technical_inspection_document_file_id", sa.UUID(), nullable=True),
        schema="ride",
    )
    op.add_column(
        "vehicles",
        sa.Column("transport_authorization_document_file_id", sa.UUID(), nullable=True),
        schema="ride",
    )
    op.add_column("vehicles", sa.Column("vehicle_photo_file_id", sa.UUID(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("registration_document_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("insurance_document_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("technical_inspection_document_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("transport_authorization_document_url", sa.Text(), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("vehicle_photo_url", sa.Text(), nullable=True), schema="ride")
    op.add_column(
        "vehicles",
        sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="active"),
        schema="ride",
    )
    op.add_column("vehicles", sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True), schema="ride")
    op.add_column("vehicles", sa.Column("review_notes", sa.Text(), nullable=True), schema="ride")
    op.create_check_constraint(
        "vehicles_verification_status_check",
        "vehicles",
        "verification_status IN ('pending_verification', 'active', 'suspended', 'rejected')",
        schema="ride",
    )


def downgrade() -> None:
    op.drop_constraint("vehicles_verification_status_check", "vehicles", schema="ride", type_="check")
    op.drop_column("vehicles", "review_notes", schema="ride")
    op.drop_column("vehicles", "reviewed_at", schema="ride")
    op.drop_column("vehicles", "verified_at", schema="ride")
    op.drop_column("vehicles", "verification_status", schema="ride")
    op.drop_column("vehicles", "vehicle_photo_url", schema="ride")
    op.drop_column("vehicles", "transport_authorization_document_url", schema="ride")
    op.drop_column("vehicles", "technical_inspection_document_url", schema="ride")
    op.drop_column("vehicles", "insurance_document_url", schema="ride")
    op.drop_column("vehicles", "registration_document_url", schema="ride")
    op.drop_column("vehicles", "vehicle_photo_file_id", schema="ride")
    op.drop_column("vehicles", "transport_authorization_document_file_id", schema="ride")
    op.drop_column("vehicles", "technical_inspection_document_file_id", schema="ride")
    op.drop_column("vehicles", "insurance_document_file_id", schema="ride")
