from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from app_base.shared_kernel.types import GeoPoint


class RouteEstimate(Protocol):
    distance_km: float
    duration_seconds: int


class GeocodeResult(Protocol):
    label: str
    point: GeoPoint


class RouteTracePoint(Protocol):
    location: GeoPoint
    recorded_at: datetime
    speed_kmh: Decimal | None
    accuracy_m: Decimal | None


class RouteTraceAnalysis(Protocol):
    actual_distance_km: Decimal | None
    actual_duration_seconds: int | None
    usable_for_scoring: bool
    recommendation: str | None
    quality_label: str | None
    quality_score: Decimal | None
    points_count: int | None
    usable_points_count: int | None


class MapProvider(Protocol):
    """Interchangeable provider for route estimates and place search."""

    async def estimate(self, origin: GeoPoint, destination: GeoPoint, profile: str) -> RouteEstimate: ...

    async def geocode(
        self,
        query: str,
        bias: GeoPoint | None = None,
        limit: int | None = None,
    ) -> list[GeocodeResult]: ...


class TraceProvider(Protocol):
    """DiddiMap-owned GPS trace lifecycle used for ride evidence and scoring."""

    async def start_trace(
        self,
        *,
        start: GeoPoint,
        end: GeoPoint,
        planned_distance_km: Decimal | None,
        planned_duration_seconds: int | None,
        profile: str,
        source_ride_id: str | None = None,
    ) -> str: ...

    async def append_trace_positions(self, trace_id: str, points: list[RouteTracePoint]) -> None: ...

    async def finish_trace(self, trace_id: str, *, finished_at: datetime) -> None: ...

    async def analyze_trace(self, trace_id: str) -> RouteTraceAnalysis: ...


class RoutingProvider(MapProvider, TraceProvider, Protocol):
    """Compatibility port for implementations supporting maps and traces."""
