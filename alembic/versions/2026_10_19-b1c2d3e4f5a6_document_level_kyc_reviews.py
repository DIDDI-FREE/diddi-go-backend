"""Separate driver KYC state and persist per-document review decisions.

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b1c2d3e4f5a6"
down_revision = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "driver_profiles",
        sa.Column("kyc_status", sa.String(30), nullable=False, server_default="pending_verification"),
        schema="ride",
    )
    op.add_column(
        "driver_profiles",
        sa.Column("kyc_document_reviews", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema="ride",
    )
    op.add_column(
        "driver_profiles",
        sa.Column("kyc_review_history", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        schema="ride",
    )
    op.add_column(
        "vehicles",
        sa.Column("document_reviews", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema="ride",
    )
    op.add_column(
        "vehicles",
        sa.Column("review_history", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        schema="ride",
    )
    op.execute(
        "UPDATE ride.driver_profiles SET kyc_status = CASE "
        "WHEN status = 'active' THEN 'approved' "
        "WHEN status = 'suspended' AND kyc_reviewed_at IS NOT NULL THEN 'rejected' "
        "ELSE 'pending_verification' END",
    )
    # Legacy KYC rejections used suspended. Keep actual suspensions untouched
    # unless a KYC decision timestamp proves the old value represented rejection.
    op.execute(
        "UPDATE ride.driver_profiles SET status = 'pending_verification' "
        "WHERE status = 'suspended' AND kyc_status = 'rejected'",
    )
    op.create_check_constraint(
        "driver_profiles_kyc_status_check",
        "driver_profiles",
        "kyc_status IN ('pending_verification', 'approved', 'rejected')",
        schema="ride",
    )


def downgrade() -> None:
    op.drop_constraint("driver_profiles_kyc_status_check", "driver_profiles", schema="ride", type_="check")
    op.drop_column("vehicles", "review_history", schema="ride")
    op.drop_column("vehicles", "document_reviews", schema="ride")
    op.drop_column("driver_profiles", "kyc_review_history", schema="ride")
    op.drop_column("driver_profiles", "kyc_document_reviews", schema="ride")
    op.drop_column("driver_profiles", "kyc_status", schema="ride")
