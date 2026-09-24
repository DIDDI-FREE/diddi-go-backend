"""Ports for durable capability projection delivery."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app_base.modules.ride.domain.capability_projection import (
    DriverCapabilityProjectionEvent,
    DriverProjectionCandidate,
)


class DriverCapabilityProjectionRepository(Protocol):
    async def enqueue(
        self, user_id: UUID, *, operational_status: str, actions: list[str], request_id: str | None,
    ) -> DriverCapabilityProjectionEvent | None: ...

    async def list_due(self, *, now: datetime, limit: int) -> list[DriverCapabilityProjectionEvent]: ...

    async def mark_succeeded(self, event: DriverCapabilityProjectionEvent, *, now: datetime) -> None: ...

    async def mark_retry(
        self, event: DriverCapabilityProjectionEvent, *, now: datetime, next_attempt_at: datetime, error: str,
    ) -> None: ...

    async def mark_conflict(self, event: DriverCapabilityProjectionEvent, *, now: datetime, error: str) -> None: ...

    async def mark_dead_letter(self, event: DriverCapabilityProjectionEvent, *, now: datetime, error: str) -> None: ...

    async def schedule_stale_refresh(self, *, before: datetime, now: datetime, limit: int) -> int: ...

    async def list_candidates(self, *, limit: int, offset: int = 0) -> list[DriverProjectionCandidate]: ...

    async def projection_metrics(self, *, now: datetime) -> dict[str, float]: ...
