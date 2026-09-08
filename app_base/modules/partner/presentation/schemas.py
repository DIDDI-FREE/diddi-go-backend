"""Pydantic schemas for partner endpoints."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PartnerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    partner_type: str
    legal_name: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, max_length=30)
    contact_email: str | None = Field(default=None, max_length=254)
    partner_commission_enabled: bool = False
    partner_commission_mode: str = "percentage"
    partner_commission_rate: Decimal = Decimal("0.00")
    registration_document_file_id: UUID | None = None
    tax_document_file_id: UUID | None = None
    representative_id_document_file_id: UUID | None = None
    fleet_ownership_document_file_id: UUID | None = None
    registration_document_url: str | None = Field(default=None, max_length=1000)
    tax_document_url: str | None = Field(default=None, max_length=1000)
    representative_id_document_url: str | None = Field(default=None, max_length=1000)
    fleet_ownership_document_url: str | None = Field(default=None, max_length=1000)


class PartnerUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    partner_type: str | None = None
    legal_name: str | None = Field(default=None, max_length=200)
    contact_phone: str | None = Field(default=None, max_length=30)
    contact_email: str | None = Field(default=None, max_length=254)
    partner_commission_enabled: bool | None = None
    partner_commission_mode: str | None = None
    partner_commission_rate: Decimal | None = None
    registration_document_file_id: UUID | None = None
    tax_document_file_id: UUID | None = None
    representative_id_document_file_id: UUID | None = None
    fleet_ownership_document_file_id: UUID | None = None
    registration_document_url: str | None = Field(default=None, max_length=1000)
    tax_document_url: str | None = Field(default=None, max_length=1000)
    representative_id_document_url: str | None = Field(default=None, max_length=1000)
    fleet_ownership_document_url: str | None = Field(default=None, max_length=1000)


class PartnerKycSubmitRequest(BaseModel):
    registration_document_file_id: UUID | None = None
    tax_document_file_id: UUID | None = None
    representative_id_document_file_id: UUID | None = None
    fleet_ownership_document_file_id: UUID | None = None
    registration_document_url: str | None = Field(default=None, max_length=1000)
    tax_document_url: str | None = Field(default=None, max_length=1000)
    representative_id_document_url: str | None = Field(default=None, max_length=1000)
    fleet_ownership_document_url: str | None = Field(default=None, max_length=1000)


class PartnerKycReviewRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class PartnerMemberCreateRequest(BaseModel):
    user_id: UUID
    role: str


class PartnerDriverAffiliateRequest(BaseModel):
    driver_id: UUID


class PartnerVehicleAssignRequest(BaseModel):
    driver_id: UUID


class PartnerVehicleCreateRequest(BaseModel):
    driver_id: UUID
    plate_number: str = Field(min_length=1, max_length=20)
    make: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=30)
    category: str = Field(default="standard")
    comfort_level: str = Field(default="standard")
    registration_document_file_id: UUID | None = None
    insurance_document_file_id: UUID | None = None
    technical_inspection_document_file_id: UUID | None = None
    transport_authorization_document_file_id: UUID | None = None
    vehicle_photo_file_id: UUID | None = None
    vehicle_front_photo_file_id: UUID | None = None
    vehicle_back_photo_file_id: UUID | None = None
    vehicle_left_photo_file_id: UUID | None = None
    vehicle_right_photo_file_id: UUID | None = None
    vehicle_interior_photo_file_id: UUID | None = None
    registration_document_url: str | None = Field(default=None, max_length=1000)
    insurance_document_url: str | None = Field(default=None, max_length=1000)
    technical_inspection_document_url: str | None = Field(default=None, max_length=1000)
    transport_authorization_document_url: str | None = Field(default=None, max_length=1000)
    vehicle_photo_url: str | None = Field(default=None, max_length=1000)
    vehicle_front_photo_url: str | None = Field(default=None, max_length=1000)
    vehicle_back_photo_url: str | None = Field(default=None, max_length=1000)
    vehicle_left_photo_url: str | None = Field(default=None, max_length=1000)
    vehicle_right_photo_url: str | None = Field(default=None, max_length=1000)
    vehicle_interior_photo_url: str | None = Field(default=None, max_length=1000)
