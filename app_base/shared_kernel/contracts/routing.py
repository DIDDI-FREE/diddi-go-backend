from __future__ import annotations

from typing import Protocol

from app_base.shared_kernel.types import GeoPoint


class RouteEstimate(Protocol):
    distance_km: float
    duration_seconds: int


class GeocodeResult(Protocol):
    label: str
    point: GeoPoint


class RoutingProvider(Protocol):
    """External routing/geocoding port. Implementations are always async since
    the underlying HTTP client is async (batch 8 uses httpx.AsyncClient)."""

    async def estimate(self, origin: GeoPoint, destination: GeoPoint, profile: str) -> RouteEstimate: ...

    async def geocode(
        self,
        query: str,
        bias: GeoPoint | None = None,
        limit: int | None = None,
    ) -> list[GeocodeResult]: ...
