"""DiddiMap core HTTP client — the `RoutingProvider` adapter.

DiddiGo never talks to OSRM/GraphHopper directly (architecture doc §5):
DiddiMap core owns the road graph, and this client is the only place in the
codebase that knows its wire format. Swapping DiddiMap for another routing
service means editing this file and nothing else.

Endpoints consumed:
    GET {base_url}/route?profile=palh_vtc&...   → distance_km, duration_seconds
    GET {base_url}/geocode?q=...                → [{label, lat, lng}, ...]

Failure policy — degrade, don't crash. If DiddiMap is unreachable, times out,
or answers with an unexpected shape, `estimate()` returns a zero-distance
result and the caller (`RideService.estimate_pricing`) falls back to its
haversine formula. A ride request must never fail because the map service
is down; the fare is approximate rather than absent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

from app_base.shared_kernel.contracts.routing import GeoPoint
from app_base.shared_kernel.types import GeoPoint as _GeoPoint

logger = logging.getLogger(__name__)

# `palh_vtc` is the VTC routing profile (palh_vtc.lua) — architecture doc §5
# requires it to be passed explicitly on every /route call.
DEFAULT_PROFILE = "palh_vtc"
DEFAULT_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class RouteEstimateResult:
    """Concrete `RouteEstimate`. Zero distance signals "no usable answer",
    which tells the pricing layer to fall back to its own calculation."""

    distance_km: float
    duration_seconds: int

    @property
    def is_usable(self) -> bool:
        return self.distance_km > 0


@dataclass(frozen=True)
class GeocodeResultItem:
    """Concrete `GeocodeResult`."""

    label: str
    point: _GeoPoint


@dataclass
class DiddiMapRoutingClient:
    base_url: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    def _http(self) -> httpx.AsyncClient:
        """Lazily build the shared connection pool. Created on first use so
        constructing the client (e.g. at import time in tests) never opens
        sockets."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url.rstrip("/"),
                timeout=self.timeout_seconds,
            )
        return self._client

    async def estimate(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        profile: str = DEFAULT_PROFILE,
    ) -> RouteEstimateResult:
        """Distance + duration for a trip. Returns a zero-distance result if
        DiddiMap cannot answer — never raises for transport-level problems."""
        params = {
            "profile": profile,
            "origin": f"{origin.lat},{origin.lng}",
            "destination": f"{destination.lat},{destination.lng}",
        }
        try:
            response = await self._http().get("/route", params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.warning(
                "DiddiMap /route unavailable (%s: %s) — pricing falls back to the local formula.",
                type(exc).__name__,
                exc,
            )
            return RouteEstimateResult(distance_km=0.0, duration_seconds=0)
        except ValueError as exc:  # malformed JSON
            logger.warning("DiddiMap /route returned invalid JSON (%s).", exc)
            return RouteEstimateResult(distance_km=0.0, duration_seconds=0)

        return self._parse_route(payload)

    async def geocode(
        self,
        query: str,
        bias: GeoPoint | None = None,
    ) -> list[GeocodeResultItem]:
        """Address → coordinates via DiddiMap's PALH geocoder. Returns an
        empty list when the service is unavailable."""
        params: dict[str, str] = {"q": query}
        if bias is not None:
            params["bias"] = f"{bias.lat},{bias.lng}"
        try:
            response = await self._http().get("/geocode", params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.warning(
                "DiddiMap /geocode unavailable (%s: %s) — returning no results.",
                type(exc).__name__,
                exc,
            )
            return []
        except ValueError as exc:
            logger.warning("DiddiMap /geocode returned invalid JSON (%s).", exc)
            return []

        return self._parse_geocode(payload)

    async def close(self) -> None:
        """Release the connection pool. Called by the app lifespan on shutdown."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # -- response parsing ---------------------------------------------------

    @staticmethod
    def _parse_route(payload: object) -> RouteEstimateResult:
        """Tolerant of both a flat `{distance_km, duration_seconds}` body and
        an OSRM-style `{routes: [{distance, duration}]}` body (meters/seconds),
        since DiddiMap may proxy either shape."""
        if not isinstance(payload, dict):
            return RouteEstimateResult(distance_km=0.0, duration_seconds=0)

        if "distance_km" in payload:
            try:
                return RouteEstimateResult(
                    distance_km=float(payload["distance_km"]),
                    duration_seconds=int(payload.get("duration_seconds", 0)),
                )
            except (TypeError, ValueError):
                logger.warning("DiddiMap /route sent unparseable distance/duration: %r", payload)
                return RouteEstimateResult(distance_km=0.0, duration_seconds=0)

        routes = payload.get("routes")
        if isinstance(routes, list) and routes and isinstance(routes[0], dict):
            first = routes[0]
            try:
                return RouteEstimateResult(
                    distance_km=float(first.get("distance", 0)) / 1000.0,
                    duration_seconds=int(float(first.get("duration", 0))),
                )
            except (TypeError, ValueError):
                logger.warning("DiddiMap /route sent an unparseable OSRM route: %r", first)

        logger.warning("DiddiMap /route returned an unrecognised shape: %r", payload)
        return RouteEstimateResult(distance_km=0.0, duration_seconds=0)

    @staticmethod
    def _parse_geocode(payload: object) -> list[GeocodeResultItem]:
        raw = payload.get("results") if isinstance(payload, dict) else payload
        if not isinstance(raw, list):
            logger.warning("DiddiMap /geocode returned an unrecognised shape: %r", payload)
            return []

        results: list[GeocodeResultItem] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            try:
                results.append(
                    GeocodeResultItem(
                        label=str(item.get("label") or item.get("name") or ""),
                        point=_GeoPoint(lat=float(item["lat"]), lng=float(item["lng"])),
                    )
                )
            except (KeyError, TypeError, ValueError):
                logger.debug("Skipping unparseable geocode entry: %r", item)
        return results
