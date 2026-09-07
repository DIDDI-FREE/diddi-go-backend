"""add partner foundation

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-09-07 09:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "f1a2b3c4d5e6"
down_revision = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS partner")
    op.create_table(
        "partners",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("partner_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending_verification"),
        sa.Column("legal_name", sa.String(length=200), nullable=True),
        sa.Column("contact_phone", sa.String(length=30), nullable=True),
        sa.Column("contact_email", sa.String(length=254), nullable=True),
        sa.Column("partner_commission_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("partner_commission_mode", sa.String(length=20), nullable=False, server_default="percentage"),
        sa.Column("partner_commission_rate", sa.Numeric(6, 4), nullable=False, server_default="0.0000"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("partner_type IN ('company', 'fleet_owner')", name="partners_partner_type_check"),
        sa.CheckConstraint(
            "status IN ('pending_verification', 'active', 'suspended', 'rejected')",
            name="partners_status_check",
        ),
        sa.CheckConstraint(
            "partner_commission_mode IN ('percentage', 'fixed')",
            name="partners_commission_mode_check",
        ),
        sa.CheckConstraint("partner_commission_rate >= 0", name="partners_commission_non_negative_check"),
        sa.CheckConstraint(
            "partner_commission_mode != 'percentage' OR partner_commission_rate <= 1",
            name="partners_percentage_commission_max_check",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="partner",
    )
    op.create_table(
        "partner_members",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "role IN ('partner_manager', 'partner_operator', 'partner_viewer')",
            name="partner_members_role_check",
        ),
        sa.ForeignKeyConstraint(["partner_id"], ["partner.partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("partner_id", "user_id", name="partner_members_partner_user_unique"),
        schema="partner",
    )
    op.create_index("ix_partner_members_partner_id", "partner_members", ["partner_id"], schema="partner")
    op.create_index("ix_partner_members_user_id", "partner_members", ["user_id"], schema="partner")

    op.add_column("vehicles", sa.Column("owner_type", sa.String(length=20), nullable=False, server_default="driver"), schema="ride")
    op.add_column("vehicles", sa.Column("partner_id", sa.UUID(), nullable=True), schema="ride")
    op.create_check_constraint("vehicles_owner_type_check", "vehicles", "owner_type IN ('driver', 'partner')", schema="ride")
    op.create_foreign_key(
        "vehicles_partner_id_fkey",
        "vehicles",
        "partners",
        ["partner_id"],
        ["id"],
        source_schema="ride",
        referent_schema="partner",
    )

    op.create_table(
        "partner_driver_links",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("driver_id", sa.UUID(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["partner_id"], ["partner.partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["driver_id"], ["ride.driver_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="partner",
    )
    op.create_index("ix_partner_driver_links_partner_id", "partner_driver_links", ["partner_id"], schema="partner")
    op.create_index("ix_partner_driver_links_driver_id", "partner_driver_links", ["driver_id"], schema="partner")
    op.create_index(
        "ux_partner_driver_links_one_active_driver",
        "partner_driver_links",
        ["driver_id"],
        unique=True,
        schema="partner",
        postgresql_where=sa.text("active = true"),
    )

    op.create_table(
        "vehicle_assignments",
        sa.Column("id", sa.UUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("partner_id", sa.UUID(), nullable=False),
        sa.Column("vehicle_id", sa.UUID(), nullable=False),
        sa.Column("driver_id", sa.UUID(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["partner_id"], ["partner.partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["ride.vehicles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["driver_id"], ["ride.driver_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="partner",
    )
    op.create_index("ix_vehicle_assignments_partner_id", "vehicle_assignments", ["partner_id"], schema="partner")
    op.create_index("ix_vehicle_assignments_vehicle_id", "vehicle_assignments", ["vehicle_id"], schema="partner")
    op.create_index("ix_vehicle_assignments_driver_id", "vehicle_assignments", ["driver_id"], schema="partner")
    op.create_index(
        "ux_vehicle_assignments_one_active_vehicle",
        "vehicle_assignments",
        ["vehicle_id"],
        unique=True,
        schema="partner",
        postgresql_where=sa.text("active = true"),
    )


def downgrade() -> None:
    op.drop_index("ux_vehicle_assignments_one_active_vehicle", table_name="vehicle_assignments", schema="partner")
    op.drop_index("ix_vehicle_assignments_driver_id", table_name="vehicle_assignments", schema="partner")
    op.drop_index("ix_vehicle_assignments_vehicle_id", table_name="vehicle_assignments", schema="partner")
    op.drop_index("ix_vehicle_assignments_partner_id", table_name="vehicle_assignments", schema="partner")
    op.drop_table("vehicle_assignments", schema="partner")
    op.drop_index("ux_partner_driver_links_one_active_driver", table_name="partner_driver_links", schema="partner")
    op.drop_index("ix_partner_driver_links_driver_id", table_name="partner_driver_links", schema="partner")
    op.drop_index("ix_partner_driver_links_partner_id", table_name="partner_driver_links", schema="partner")
    op.drop_table("partner_driver_links", schema="partner")
    op.drop_constraint("vehicles_partner_id_fkey", "vehicles", schema="ride", type_="foreignkey")
    op.drop_constraint("vehicles_owner_type_check", "vehicles", schema="ride", type_="check")
    op.drop_column("vehicles", "partner_id", schema="ride")
    op.drop_column("vehicles", "owner_type", schema="ride")
    op.drop_index("ix_partner_members_user_id", table_name="partner_members", schema="partner")
    op.drop_index("ix_partner_members_partner_id", table_name="partner_members", schema="partner")
    op.drop_table("partner_members", schema="partner")
    op.drop_table("partners", schema="partner")
    op.execute("DROP SCHEMA IF EXISTS partner")
