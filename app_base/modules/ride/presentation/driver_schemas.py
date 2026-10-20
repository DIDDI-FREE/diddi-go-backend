"""Pydantic schemas for driver onboarding and availability."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

DocumentType = Literal[
    "license_front",
    "license_back",
    "national_id_front",
    "national_id_back",
    "selfie",
    "registration",
    "insurance",
    "technical_inspection",
    "transport_authorization",
    "vehicle_front",
    "vehicle_back",
    "vehicle_left",
    "vehicle_right",
    "vehicle_interior",
    "vehicle_plate",
]


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
    make: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
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
    """Edit a vehicle's descriptive fields.

    Documents are corrected through the KYV resubmission flow and the vehicle's
    verification status is preserved.
    """

    plate_number: str = Field(min_length=1, max_length=20)
    make: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
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
    document_type: DocumentType
    decision: Literal["approved", "rejected"]
    reason_code: str | None = Field(default=None, min_length=1, max_length=80)
    reason: str | None = Field(default=None, min_length=3, max_length=1000)
    expected_correction: str | None = Field(default=None, min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validate_rejection_details(self) -> DocumentReviewDecision:
        if self.decision == "rejected" and not all((self.reason_code, self.reason, self.expected_correction)):
            raise ValueError(
                "A rejected document requires reason_code, reason and expected_correction.",
            )
        return self


class DriverKycReviewRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)
    documents: list[DocumentReviewDecision] = Field(default_factory=list, max_length=20)


class DriverKycApproveRequest(DriverKycReviewRequest):
    @model_validator(mode="after")
    def approvals_only(self) -> DriverKycApproveRequest:
        if any(item.decision != "approved" for item in self.documents):
            raise ValueError("The approval route only accepts approved document decisions.")
        return self


class DriverKycRejectRequest(DriverKycReviewRequest):
    documents: list[DocumentReviewDecision] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def contains_rejection(self) -> DriverKycRejectRequest:
        if not any(item.decision == "rejected" for item in self.documents):
            raise ValueError("The rejection route requires at least one rejected document.")
        return self


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
    verification_status: Literal[
        "pending_verification",
        "active",
        "suspended",
        "rejected",
    ]
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
    rating_avg: float
    rating_count: int
    rating_status: Literal["new", "rated"]
    profile_photo_file_id: UUID | None = None
    kyc: DriverKycResponse
    vehicle: VehicleResponse | None = None
