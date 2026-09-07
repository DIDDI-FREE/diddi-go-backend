"""Partner module PostgreSQL models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app_base.core.database import Base

_PG_UUID = PG_UUID(as_uuid=True)


class PartnerModel(Base):
    __tablename__ = "partners"
    __table_args__ = {"schema": "partner"}

    id: Mapped[UUID] = mapped_column(_PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    partner_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending_verification")
    legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    partner_commission_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    partner_commission_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="percentage")
    partner_commission_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0.0000"))
    registration_document_file_id: Mapped[UUID | None] = mapped_column(_PG_UUID, nullable=True)
    tax_document_file_id: Mapped[UUID | None] = mapped_column(_PG_UUID, nullable=True)
    representative_id_document_file_id: Mapped[UUID | None] = mapped_column(_PG_UUID, nullable=True)
    fleet_ownership_document_file_id: Mapped[UUID | None] = mapped_column(_PG_UUID, nullable=True)
    registration_document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    tax_document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    representative_id_document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    fleet_ownership_document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    kyc_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    kyc_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    kyc_review_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class PartnerMemberModel(Base):
    __tablename__ = "partner_members"
    __table_args__ = (
        UniqueConstraint("partner_id", "user_id", name="partner_members_partner_user_unique"),
        {"schema": "partner"},
    )

    id: Mapped[UUID] = mapped_column(_PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    partner_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("partner.partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(_PG_UUID, ForeignKey("auth.users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class PartnerDriverLinkModel(Base):
    __tablename__ = "partner_driver_links"
    __table_args__ = {"schema": "partner"}

    id: Mapped[UUID] = mapped_column(_PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    partner_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("partner.partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    driver_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("ride.driver_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VehicleAssignmentModel(Base):
    __tablename__ = "vehicle_assignments"
    __table_args__ = {"schema": "partner"}

    id: Mapped[UUID] = mapped_column(_PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    partner_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("partner.partners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vehicle_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("ride.vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    driver_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("ride.driver_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
