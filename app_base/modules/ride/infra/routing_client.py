"""DiddiMap/AbidjanMaps HTTP adapter.

DiddiMap is the single provider of geographic truth for DiddiGo: route
distance, duration, and place search. If DiddiMap is unavailable or returns an
unexpected payload, this adapter raises an ApiError. It must never fabricate a
silent fallback distance, duration, or geocode result.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx

from app_base.core.errors import ApiError
from app_base.shared_kernel.contracts.routing import GeoPoint
from app_base.shared_kernel.types import GeoPoint as _GeoPoint

logger = logging.getLogger(__name__)

# Business profile kept for DiddiGo callers. AbidjanMaps staging currently
# supports "car", so we translate until it exposes a dedicated VTC profile.
DEFAULT_PROFILE = "palh_vtc"
DEFAULT_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class RouteEstimateResult:
    distance_km: float
    duration_seconds: int

    @property
    def is_usable(self) -> bool:
        return self.distance_km > 0


@dataclass(frozen=True)
class GeocodeResultItem:
    label: str
    point: _GeoPoint


@dataclass
class DiddiMapRoutingClient:
    base_url: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    def _http(self) -> httpx.AsyncClient:
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
        request_payload = {
            "profile": _abidjanmaps_profile(profile),
            "start": {"lat": origin.lat, "lng": origin.lng},
            "end": {"lat": destination.lat, "lng": destination.lng},
        }
        try:
            response = await self._http().post("/api/v1/route", json=request_payload)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.exception("DiddiMap route unavailable: %s", exc)
            raise ApiError(503, "DIDDIMAP_UNAVAILABLE", "Service geographique indisponible.") from exc
        except ValueError as exc:
            logger.exception("DiddiMap route returned invalid JSON: %s", exc)
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Reponse geographique invalide.") from exc

        return self._parse_route(payload)

    async def geocode(
        self,
        query: str,
        bias: GeoPoint | None = None,
        limit: int | None = None,
    ) -> list[GeocodeResultItem]:
        params: dict[str, str] = {"q": query}
        if bias is not None:
            params["bias_lat"] = str(bias.lat)
            params["bias_lng"] = str(bias.lng)
        if limit is not None:
            params["limit"] = str(limit)
        try:
            response = await self._http().get("/api/v1/geocoding/search", params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.exception("DiddiMap geocoding unavailable: %s", exc)
            raise ApiError(503, "DIDDIMAP_UNAVAILABLE", "Service geographique indisponible.") from exc
        except ValueError as exc:
            logger.exception("DiddiMap geocoding returned invalid JSON: %s", exc)
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Reponse geographique invalide.") from exc

        return self._parse_geocode(payload)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def _parse_route(payload: object) -> RouteEstimateResult:
        if not isinstance(payload, dict):
            logger.error("DiddiMap route returned non-object payload: %r", payload)
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Format route DiddiMap non reconnu.")

        if "distance_km" in payload:
            try:
                return RouteEstimateResult(
                    distance_km=float(payload["distance_km"]),
                    duration_seconds=int(payload.get("duration_seconds", 0)),
                )
            except (TypeError, ValueError) as exc:
                logger.exception("DiddiMap route sent invalid distance/duration: %r", payload)
                raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Distance ou duree DiddiMap invalide.") from exc

        route = payload.get("route")
        if isinstance(route, dict):
            try:
                return RouteEstimateResult(
                    distance_km=float(route["distance_m"]) / 1000.0,
                    duration_seconds=int(float(route["duration_s"])),
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.exception("DiddiMap route sent invalid AbidjanMaps route: %r", route)
                raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Route DiddiMap invalide.") from exc

        routes = payload.get("routes")
        if isinstance(routes, list) and routes and isinstance(routes[0], dict):
            first = routes[0]
            try:
                return RouteEstimateResult(
                    distance_km=float(first["distance"]) / 1000.0,
                    duration_seconds=int(float(first["duration"])),
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.exception("DiddiMap route sent invalid OSRM route: %r", first)
                raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Route DiddiMap invalide.") from exc

        logger.error("DiddiMap route returned unrecognised payload: %r", payload)
        raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Format route DiddiMap non reconnu.")

    @staticmethod
    def _parse_geocode(payload: object) -> list[GeocodeResultItem]:
        raw = payload.get("results") if isinstance(payload, dict) else payload
        if not isinstance(raw, list):
            logger.error("DiddiMap geocoding returned unrecognised payload: %r", payload)
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Format geocodage DiddiMap non reconnu.")

        results: list[GeocodeResultItem] = []
        for item in raw:
            if not isinstance(item, dict):
                logger.warning("Skipping malformed DiddiMap geocode item: %r", item)
                continue
            location = item.get("location") if isinstance(item.get("location"), dict) else item
            try:
                results.append(
                    GeocodeResultItem(
                        label=str(item.get("label") or item.get("name") or ""),
                        point=_GeoPoint(lat=float(location["lat"]), lng=float(location["lng"])),
                    )
                )
            except (KeyError, TypeError, ValueError):
                logger.warning("Skipping malformed DiddiMap geocode item: %r", item)
        return results


def _abidjanmaps_profile(profile: str) -> str:
    if profile == DEFAULT_PROFILE:
        return "car"
    return profile
