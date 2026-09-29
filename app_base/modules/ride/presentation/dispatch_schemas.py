"""Request/response models for the S2S dispatch admin API (SCRUM-63)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app_base.modules.ride.domain.priority import DispatchConfig


class DispatchConfigBody(BaseModel):
    """Full dispatch tunables — GET returns it, PUT replaces it (UC-288)."""

    search_radius_km: float = Field(gt=0)
    search_radius_step_km: float = Field(ge=0)
    search_radius_max_km: float = Field(gt=0)
    offer_wave_size: int = Field(ge=1, le=50)
    search_budget_seconds: int = Field(ge=0, le=3600)
    eta_shortlist_size: int = Field(ge=1, le=100)
    priority_window_days: int = Field(ge=1, le=365)
    priority_cap_seconds: int = Field(ge=0, le=3600)
    priority_seconds_per_point: int = Field(ge=0, le=3600)
    points_ride_completed: int = Field(ge=-1000, le=1000)
    points_ride_cancelled_by_driver: int = Field(ge=-1000, le=1000)

    @classmethod
    def from_config(cls, config: DispatchConfig) -> DispatchConfigBody:
        return cls(**vars(config))

    def to_config(self) -> DispatchConfig:
        return DispatchConfig(**self.model_dump())


class PriorityBoostRequest(BaseModel):
    """Grant an expiring priority boost to a driver (UC-106)."""

    driver_id: UUID
    points: int = Field(gt=0, le=1000)
    duration_minutes: int = Field(gt=0, le=10080)
    reason: str = Field(min_length=1, max_length=200)


class PriorityEventView(BaseModel):
    driver_id: UUID
    kind: str
    points: int
    zone_id: UUID | None
    ride_id: UUID | None
    reason: str | None
    expires_at: datetime | None
