"""driver_kyc_file_ids

Revision ID: c4a2d8f1e9b7
Revises: b3f6c2a9d8e1
Create Date: 2026-08-05
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "c4a2d8f1e9b7"
down_revision = "b3f6c2a9d8e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "driver_profiles",
        sa.Column("license_document_file_id", sa.UUID(), nullable=True),
        schema="ride",
    )
    op.add_column(
        "driver_profiles",
        sa.Column("national_id_document_file_id", sa.UUID(), nullable=True),
        schema="ride",
    )
    op.add_column(
        "driver_profiles",
        sa.Column("selfie_document_file_id", sa.UUID(), nullable=True),
        schema="ride",
    )
    op.add_column(
        "vehicles",
        sa.Column("registration_document_file_id", sa.UUID(), nullable=True),
        schema="ride",
    )


def downgrade() -> None:
    op.drop_column("vehicles", "registration_document_file_id", schema="ride")
    op.drop_column("driver_profiles", "selfie_document_file_id", schema="ride")
    op.drop_column("driver_profiles", "national_id_document_file_id", schema="ride")
    op.drop_column("driver_profiles", "license_document_file_id", schema="ride")
