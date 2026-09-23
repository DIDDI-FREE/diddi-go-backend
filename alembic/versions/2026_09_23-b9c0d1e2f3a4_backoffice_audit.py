"""Add persistent Backoffice command audit events.

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-09-23 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b9c0d1e2f3a4"
down_revision: str | None = "a8b9c0d1e2f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")
    op.create_table(
        "backoffice_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("client_id", sa.String(length=120), nullable=False),
        sa.Column("service_subject", sa.String(length=160), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idempotency_key", sa.String(length=160), nullable=False),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "action", "idempotency_key", name="uq_audit_backoffice_command"),
        schema="audit",
    )
    op.create_index(
        "idx_audit_backoffice_target_created",
        "backoffice_events",
        ["target_type", "target_id", "created_at"],
        schema="audit",
    )
    op.create_index(
        "idx_audit_backoffice_actor_created",
        "backoffice_events",
        ["actor_user_id", "created_at"],
        schema="audit",
    )


def downgrade() -> None:
    op.drop_index("idx_audit_backoffice_actor_created", table_name="backoffice_events", schema="audit")
    op.drop_index("idx_audit_backoffice_target_created", table_name="backoffice_events", schema="audit")
    op.drop_table("backoffice_events", schema="audit")
    op.execute("DROP SCHEMA IF EXISTS audit")
