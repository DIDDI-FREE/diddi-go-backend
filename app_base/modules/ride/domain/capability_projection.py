"""Durable DiddiFreeID capability projection state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DriverCapabilityProjectionEvent:
    user_id: UUID
    projection_version: int
    operational_status: str
    actions: list[str]
    event_id: str
    request_id: str | None = None
    status: str = "pending"
    attempts: int = 0
    next_attempt_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class DriverProjectionCandidate:
    user_id: UUID
    profile_status: str
    vehicle_status: str | None
    vehicle_active: bool | None
