"""Queue of driver access statuses to send to DiddiFreeID (ticket 084).

DiddiGo tells DiddiFreeID when a driver becomes `enabled`, `suspended` or `rejected`
(decision 2026-11-26-professional-validation-is-recorded-in-diddifreeid). Each change is
kept here and sent until DiddiFreeID accepts it. A one-time back-fill adds rows with the
driver's real approval date in `enabled_at`.
"""

from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "driver_access_status_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.String(length=200), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("access_status", sa.String(length=30), nullable=False),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.String(length=180), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_driver_access_status_event_id"),
        schema="ride",
    )
    op.create_index(
        "idx_driver_access_status_due", "driver_access_status_events", ["status", "next_attempt_at"], schema="ride"
    )
    op.create_index(
        "idx_driver_access_status_user", "driver_access_status_events", ["user_id", "created_at"], schema="ride"
    )


def downgrade() -> None:
    op.drop_index("idx_driver_access_status_user", table_name="driver_access_status_events", schema="ride")
    op.drop_index("idx_driver_access_status_due", table_name="driver_access_status_events", schema="ride")
    op.drop_table("driver_access_status_events", schema="ride")
