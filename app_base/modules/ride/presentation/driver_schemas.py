"""Pydantic schemas for driver onboarding and availability."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DriverProfileCreateRequest(BaseModel):
    license_number: str = Field(min_length=1, max_length=50)
    legal_name: str | None = Field(default=None, min_length=1, max_length=160)
    birth_date: date | None = None
    residence_address: str | None = Field(default=None, min_length=1, max_length=500)
    license_document_file_id: UUID | None = None
    license_back_document_file_id: UUID | None = None
    national_id_document_file_id: UUID | None = None
    national_id_back_document_file_id: UUID | None = None
    selfie_document_file_id: UUID | None = None
    profile_photo_file_id: UUID | None = None
    license_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    license_back_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    national_id_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    national_id_back_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    selfie_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    license_expires_at: datetime | None = None
    national_id_expires_at: datetime | None = None


class DriverProvisionRequest(DriverProfileCreateRequest):
    user_id: UUID
    full_name: str | None = Field(default=None, min_length=1, max_length=120)


class DriverProfilePhotoUpdateRequest(BaseModel):
    profile_photo_file_id: UUID


class DriverKycResubmitRequest(BaseModel):
    license_number: str | None = Field(default=None, min_length=1, max_length=50)
    legal_name: str | None = Field(default=None, min_length=1, max_length=160)
    birth_date: date | None = None
    residence_address: str | None = Field(default=None, min_length=1, max_length=500)
    license_document_file_id: UUID | None = None
    license_back_document_file_id: UUID | None = None
    national_id_document_file_id: UUID | None = None
    national_id_back_document_file_id: UUID | None = None
    selfie_document_file_id: UUID | None = None
    profile_photo_file_id: UUID | None = None
    license_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    license_back_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    national_id_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    national_id_back_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    selfie_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    license_expires_at: datetime | None = None
    national_id_expires_at: datetime | None = None


class VehicleCreateRequest(BaseModel):
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
    vehicle_plate_photo_file_id: UUID | None = None
    registration_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    insurance_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    technical_inspection_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    transport_authorization_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_front_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_back_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_left_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_right_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_interior_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_plate_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)


class VehicleUpdateRequest(BaseModel):
    """Edit a vehicle's descriptive fields after KYC (SCRUM-524 #1). Documents
    go through the kyv/resubmit flow, not here."""

    plate_number: str = Field(min_length=1, max_length=20)
    make: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=30)
    category: str = Field(default="standard")


class VehicleKyvResubmitRequest(BaseModel):
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
    vehicle_plate_photo_file_id: UUID | None = None
    registration_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    insurance_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    technical_inspection_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    transport_authorization_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_front_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_back_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_left_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_right_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_interior_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)
    vehicle_plate_photo_url: str | None = Field(default=None, min_length=1, max_length=1000)


class GoOnlineRequest(BaseModel):
    """A driver announces availability with their current position, so they
    enter the matching pool immediately rather than only after the first
    WebSocket location push."""

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class DocumentReviewDecision(BaseModel):
    document_type: str = Field(min_length=1, max_length=80)
    decision: Literal["approved", "rejected"]
    reason_code: str | None = Field(default=None, min_length=1, max_length=80)
    reason: str | None = Field(default=None, min_length=3, max_length=1000)
    expected_correction: str | None = Field(default=None, min_length=3, max_length=1000)


class DriverKycReviewRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)
    documents: list[DocumentReviewDecision] = Field(default_factory=list, max_length=20)


class DocumentReviewResponse(BaseModel):
    document_type: str
    status: Literal["pending", "approved", "rejected"]
    reason_code: str | None = None
    reason: str | None = None
    expected_correction: str | None = None
    reviewed_at: datetime | None = None


class DriverKycResponse(BaseModel):
    status: Literal["pending_verification", "approved", "rejected"]
    legal_name: str | None = None
    birth_date: date | None = None
    residence_address: str | None = None
    license_document_file_id: UUID | None = None
    license_back_document_file_id: UUID | None = None
    national_id_document_file_id: UUID | None = None
    national_id_back_document_file_id: UUID | None = None
    selfie_document_file_id: UUID | None = None
    license_document_url: str | None = None
    license_back_document_url: str | None = None
    national_id_document_url: str | None = None
    national_id_back_document_url: str | None = None
    selfie_document_url: str | None = None
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    document_reviews: list[DocumentReviewResponse] = Field(default_factory=list)
    license_expires_at: datetime | None = None
    national_id_expires_at: datetime | None = None
    documents_expiry_status: Literal["valid", "expiring_soon", "expired"]


class VehicleResponse(BaseModel):
    id: UUID
    driver_id: UUID
    plate_number: str
    make: str | None = None
    model: str | None = None
    color: str | None = None
    category: str
    comfort_level: str
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
    vehicle_plate_photo_file_id: UUID | None = None
    registration_document_url: str | None = None
    insurance_document_url: str | None = None
    technical_inspection_document_url: str | None = None
    transport_authorization_document_url: str | None = None
    vehicle_photo_url: str | None = None
    vehicle_front_photo_url: str | None = None
    vehicle_back_photo_url: str | None = None
    vehicle_left_photo_url: str | None = None
    vehicle_right_photo_url: str | None = None
    vehicle_interior_photo_url: str | None = None
    vehicle_plate_photo_url: str | None = None
    verification_status: str
    verified_at: datetime | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    document_reviews: list[DocumentReviewResponse] = Field(default_factory=list)
    owner_type: str
    partner_id: UUID | None = None
    active: bool


class DriverProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    license_number: str
    status: str
    rating_avg: float | None = None
    rating_count: int
    profile_photo_file_id: UUID | None = None
    kyc: DriverKycResponse
    vehicle: VehicleResponse | None = None
