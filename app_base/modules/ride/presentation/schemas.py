"""Pydantic request/response schemas for the ride endpoints.

Shape matches the API contract (`DiddiGo_Contrat_API.md` §2):
  - `PointPayload` is shared between pricing estimate and ride creation.
  - `RideCreateRequest.scheduled_at` accepts ISO 8601 or null (immediate ride).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PointPayload(BaseModel):
    lat: float
    lng: float
    address: str | None = None


class PlaceSearchResponseItem(BaseModel):
    label: str
    lat: float
    lng: float


class PricingEstimateRequest(BaseModel):
    pickup: PointPayload
    dropoff: PointPayload
    vehicle_category: str = Field(default="standard")
    comfort_level: str = Field(default="standard")


class RideCreateRequest(BaseModel):
    pickup: PointPayload
    dropoff: PointPayload
    vehicle_category: str = Field(default="standard")
    comfort_level: str = Field(default="standard")
    payment_method: str = Field(default="cash")
    scheduled_at: datetime | None = None  # null = ride immédiat, sinon ISO 8601


class RideStatusUpdateRequest(BaseModel):
    status: str


class RideCancelRequest(BaseModel):
    reason: str


class RideRatingRequest(BaseModel):
    rating: int
    comment: str | None = None


class RideLocationSamplePayload(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    recorded_at: datetime | None = None
    heading: int | None = Field(default=None, ge=0, le=359)
    speed_kmh: float | None = Field(default=None, ge=0)
    accuracy_m: float | None = Field(default=None, ge=0)
    source: str = Field(default="driver")


class RideLocationSamplesRequest(BaseModel):
    samples: list[RideLocationSamplePayload] = Field(min_length=1, max_length=120)


class RideEmergencyRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)
