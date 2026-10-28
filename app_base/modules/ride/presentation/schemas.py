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
    custom_label: str | None = Field(default=None, min_length=1, max_length=120)
    reason: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def normalize_legacy_reason(self) -> RideSupplementCreateRequest:
        # `reason` was the original category field. Keep accepting it during
        # the migration while exposing the clearer `type` contract.
        if self.type is None:
            self.type = self.reason
        if self.type is None:
            raise ValueError("type is required")
        if self.type.strip().lower() == "other" and self.custom_label is None:
            raise ValueError("custom_label is required when type is other")
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


class RidePointResponse(BaseModel):
    lat: float | None = None
    lng: float | None = None
    address: str | None = None


class RidePassengerResponse(BaseModel):
    id: UUID
    full_name: str | None = None


class RideVehiclePublicResponse(BaseModel):
    make: str | None = None
    model: str | None = None
    color: str | None = None
    plate_number: str | None = None
    category: str
    comfort_level: str


class RideDriverResponse(BaseModel):
    id: UUID
    full_name: str | None = None
    rating_avg: float
    rating_count: int
    rating_status: Literal["new", "rated"]
    phone: str | None = None
    photo_url: str | None = None
    vehicle: RideVehiclePublicResponse | None = None


class RidePricingResponse(BaseModel):
    base_fare: int | None = None
    distance_fare: int | None = None
    duration_fare: int | None = None
    surge_multiplier: float
    surge_cap: float
    commission_rate: float
    comfort_multiplier: float
    platform_commission: int | None = None
    driver_payout_estimate: int | None = None
    actual_distance_km: float | None = None
    actual_duration_seconds: int | None = None
    actual_pricing_fare: int | None = None
    pricing_delta: int | None = None
    waiting_fee: int | None = None
    waiting_rate_per_minute: int | None = None


class RideTraceAnalysisResponse(BaseModel):
    status: str
    error_code: str | None = None
    recommendation: str | None = None
    quality_label: str | None = None
    quality_score: float | None = None
    points_count: int | None = None
    usable_points_count: int | None = None


class RideWaitingResponse(BaseModel):
    active: bool
    started_at: datetime | None = None
    duration_seconds: int
    fee: int | None = None
    rate_per_minute: int | None = None


class RidePaymentResponse(BaseModel):
    method: Literal["cash", "mobile_money"]
    transaction_id: UUID | None = None
    ready: bool


class RideEarlyStopResponse(BaseModel):
    requested_at: datetime | None = None
    expires_at: datetime | None = None
    confirmed_at: datetime | None = None


class RideStartAuthorizationResponse(BaseModel):
    code: str | None = None
    qr_payload: str | None = None
    attempts: int | None = None
    blocked: bool
    used_at: datetime | None = None


class RideEmergencyResponse(BaseModel):
    status: str | None = None
    requested_at: datetime | None = None


class RideDetailResponse(BaseModel):
    """Canonical read model returned by ride detail and active-ride recovery."""

    id: UUID
    status: str
    completion_reason: str | None = None
    passenger: RidePassengerResponse
    driver: RideDriverResponse | None = None
    pickup: RidePointResponse
    dropoff: RidePointResponse
    vehicle_category: str
    comfort_level: str
    estimated_fare: int | None = None
    final_fare: int | None = None
    currency: str
    distance_km: float | None = None
    duration_seconds: int | None = None
    pricing: RidePricingResponse
    trace_analysis: RideTraceAnalysisResponse
    waiting: RideWaitingResponse
    payment: RidePaymentResponse
    quote_id: UUID | None = None
    early_stop: RideEarlyStopResponse
    arrival: RideArrivalResponse
    start_authorization: RideStartAuthorizationResponse
    emergency: RideEmergencyResponse
    requested_at: datetime | None = None
    matched_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class DriverVehicleCapabilityResponse(BaseModel):
    id: UUID
    status: str
    active: bool
    category: str
    comfort_level: str
    owner_type: str
    partner_id: UUID | None = None


class DriverProfessionalProfileResponse(BaseModel):
    type: Literal["driver"]
    exists: bool
    status: str
    verification_status: str
    can_go_online: bool
    blocking_reasons: list[str]
    driver_profile_id: UUID | None = None
    vehicle: DriverVehicleCapabilityResponse | None = None
    score: float | None = None
    online_requirements: dict[str, dict] | None = None


class ConsumerCapabilityResponse(BaseModel):
    type: Literal["passenger"]
    enabled: bool
    status: str
    blocking_reasons: list[str]


class ProMetiersResponse(BaseModel):
    scope: Literal["diddigo_local"]
    user_id: UUID
    metiers: list[DriverProfessionalProfileResponse]
    consumer: ConsumerCapabilityResponse


class RideSupplementResponse(BaseModel):
    id: UUID
    ride_id: UUID
    amount: int
    reason: str
    type: Literal["toll", "parking", "baggage_standard", "baggage_large", "other"]
    custom_label: str | None = None
    source: Literal["catalog"]
    status: Literal["pending", "accepted", "disputed"]
    created_by_user_id: UUID | None = None
    created_at: datetime | None = None
    decided_by_user_id: UUID | None = None
    decided_at: datetime | None = None


class RideSupplementListResponse(BaseModel):
    items: list[RideSupplementResponse]
    supplements_total: int


class RideSupplementCatalogItem(BaseModel):
    type: Literal["toll", "parking", "baggage_standard", "baggage_large", "other"]
    label: str
    amount_xof: int | None = None
    minimum_amount_xof: int | None = None
    maximum_amount_xof: int | None = None
    requires_custom_label: bool = False


class RideSupplementCatalogResponse(BaseModel):
    currency: Literal["XOF"]
    items: list[RideSupplementCatalogItem]


class RideEmergencyRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class EmergencyContactUpsertRequest(BaseModel):
    contact_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=254)
    relationship: str | None = Field(default=None, max_length=80)
