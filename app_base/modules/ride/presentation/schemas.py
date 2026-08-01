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


class RideCreateRequest(BaseModel):
    pickup: PointPayload
    dropoff: PointPayload
    vehicle_category: str = Field(default="standard")
    scheduled_at: datetime | None = None  # null = ride immédiat, sinon ISO 8601


class RideStatusUpdateRequest(BaseModel):
    status: str


class RideCancelRequest(BaseModel):
    reason: str


class RideRatingRequest(BaseModel):
    rating: int
    comment: str | None = None
