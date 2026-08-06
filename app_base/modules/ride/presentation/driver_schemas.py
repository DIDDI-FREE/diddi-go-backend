"""Pydantic schemas for driver onboarding and availability."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class DriverProfileCreateRequest(BaseModel):
    license_number: str = Field(min_length=1, max_length=50)
    legal_name: str | None = Field(default=None, min_length=1, max_length=160)
    birth_date: date | None = None
    residence_address: str | None = Field(default=None, min_length=1, max_length=500)
    license_document_file_id: UUID | None = None
    national_id_document_file_id: UUID | None = None
    selfie_document_file_id: UUID | None = None
    license_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    national_id_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    selfie_document_url: str | None = Field(default=None, min_length=1, max_length=1000)


class DriverKycResubmitRequest(BaseModel):
    license_number: str | None = Field(default=None, min_length=1, max_length=50)
    legal_name: str | None = Field(default=None, min_length=1, max_length=160)
    birth_date: date | None = None
    residence_address: str | None = Field(default=None, min_length=1, max_length=500)
    license_document_file_id: UUID | None = None
    national_id_document_file_id: UUID | None = None
    selfie_document_file_id: UUID | None = None
    license_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    national_id_document_url: str | None = Field(default=None, min_length=1, max_length=1000)
    selfie_document_url: str | None = Field(default=None, min_length=1, max_length=1000)


class VehicleCreateRequest(BaseModel):
    plate_number: str = Field(min_length=1, max_length=20)
    make: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=30)
    category: str = Field(default="standard")
    comfort_level: str = Field(default="standard")
    registration_document_file_id: UUID | None = None


class GoOnlineRequest(BaseModel):
    """A driver announces availability with their current position, so they
    enter the matching pool immediately rather than only after the first
    WebSocket location push."""

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class DriverKycReviewRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)
