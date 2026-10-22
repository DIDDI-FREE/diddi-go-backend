"""Pydantic request/response schemas for the ride endpoints.

Shape matches the API contract (`DiddiGo_Contrat_API.md` §2):
  - `PointPayload` is shared between pricing estimate and ride creation.
  - `RideCreateRequest.scheduled_at` accepts ISO 8601 or null (immediate ride).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PointPayload(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
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
    quote_id: UUID
    payment_method: Literal["cash", "mobile_money"] = "cash"
    scheduled_at: datetime | None = None  # null = ride immédiat, sinon ISO 8601


class RideStatusUpdateRequest(BaseModel):
    status: str


class EarlyStopResponse(BaseModel):
    ride_id: UUID
    status: str
    completion_reason: str | None = None
    requested_at: datetime | None = None
    expires_at: datetime | None = None
    confirmed_at: datetime | None = None
    provisional: bool
    amount: int
    currency: str


class RideStartRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class RideCancelRequest(BaseModel):
    reason: str


class RideRatingRequest(BaseModel):
    # Keep range validation in the application service so callers receive the
    # documented business error envelope instead of a generic schema error.
    rating: int
    comment: str | None = None


class PersonalScoreMetricsResponse(BaseModel):
    total_rides: int
    eligible_rides: int
    completed_rides: int
    cancelled_rides: int
    emergency_reports: int
    rating_count: int
    rating_avg: float | None = None
    completion_rate: float
    cancellation_rate: float


class PersonalScoreResponse(BaseModel):
    subject_type: Literal["passenger", "driver"]
    subject_id: UUID
    score_value: float
    score_level: Literal["new", "excellent", "good", "fair", "risk"]
    score_status: Literal["insufficient_data", "stable"]
    reason_codes: list[str]
    last_calculated_at: datetime
    sample_size: int
    metrics: PersonalScoreMetricsResponse


class MyScoresResponse(BaseModel):
    user_id: UUID
    service: Literal["diddigo"]
    passenger_score: PersonalScoreResponse
    driver_score: PersonalScoreResponse | None = None


class RideScoreMetricsResponse(BaseModel):
    ride_status: str
    rating_count: int
    rating_avg: float | None = None
    emergency_status: str | None = None
    cancellation_reason: str | None = None


class RideScoreResponse(BaseModel):
    ride_id: UUID
    subject_type: Literal["trip"]
    score_value: float
    score_level: Literal["new", "excellent", "good", "fair", "risk"]
    score_status: Literal["provisional", "stable"]
    reason_codes: list[str]
    last_calculated_at: datetime
    sample_size: int
    metrics: RideScoreMetricsResponse


class RideRatingResponse(BaseModel):
    id: UUID
    ride_id: UUID
    rating: int
    rater_role: Literal["passenger", "driver"]


class RideStopCreateRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=500)


class RideSupplementCreateRequest(BaseModel):
    type: str | None = Field(default=None, min_length=1, max_length=40)
    amount: Decimal | None = Field(default=None, gt=0)
    reason: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def normalize_legacy_reason(self) -> RideSupplementCreateRequest:
        # `reason` was the original category field. Keep accepting it during
        # the migration while exposing the clearer `type` contract.
        if self.type is None:
            self.type = self.reason
        if self.type is None:
            raise ValueError("type is required")
        return self


class RideSupplementDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(accepted|disputed)$")


class RideLocationSamplePayload(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    recorded_at: datetime | None = None
    heading: int | None = Field(default=None, ge=0, le=359)
    speed_kmh: float | None = Field(default=None, ge=0)
    accuracy_m: float | None = Field(default=None, ge=0)
    source: str = Field(default="driver")


class RideLocationSamplesRequest(BaseModel):
    batch_id: UUID | None = None
    samples: list[RideLocationSamplePayload] = Field(min_length=1, max_length=120)


class RideLocationSamplesResponse(BaseModel):
    ride_id: UUID
    batch_id: UUID
    accepted_samples: int
    replayed: bool


class PreRideArrivalResponse(BaseModel):
    ride_id: UUID
    status: str
    arrived_at: datetime
    waiting_started_at: datetime
    free_seconds: int
    no_show_after_seconds: int
    price_per_minute_xof: int


class RideArrivalResponse(BaseModel):
    """Arrival and pre-departure waiting settings, safe to restore after reconnect."""

    arrived_at: datetime | None = None
    waiting_started_at: datetime | None = None
    waiting_seconds: int
    waiting_fee: int | None = None
    free_seconds: int
    price_per_minute_xof: int
    no_show_after_seconds: int


class RideSupplementResponse(BaseModel):
    id: UUID
    ride_id: UUID
    amount: int
    reason: str
    type: Literal["toll", "parking", "baggage_standard", "baggage_large", "other"]
    source: Literal["catalog"]
    status: Literal["pending", "accepted", "disputed"]
    created_by_user_id: UUID | None = None
    created_at: datetime | None = None
    decided_by_user_id: UUID | None = None
    decided_at: datetime | None = None


class RideSupplementListResponse(BaseModel):
    items: list[RideSupplementResponse]
    supplements_total: int


class RideEmergencyRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class EmergencyContactUpsertRequest(BaseModel):
    contact_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    relationship: str | None = Field(default=None, max_length=80)
