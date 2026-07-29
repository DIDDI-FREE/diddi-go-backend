"""Pydantic schemas for driver onboarding and availability."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DriverProfileCreateRequest(BaseModel):
    license_number: str = Field(min_length=1, max_length=50)


class VehicleCreateRequest(BaseModel):
    plate_number: str = Field(min_length=1, max_length=20)
    make: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, max_length=30)
    category: str = Field(default="standard")


class GoOnlineRequest(BaseModel):
    """A driver announces availability with their current position, so they
    enter the matching pool immediately rather than only after the first
    WebSocket location push."""

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
