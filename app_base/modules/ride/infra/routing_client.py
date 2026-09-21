"""DiddiMap/AbidjanMaps HTTP adapter.

DiddiMap is the single provider of geographic truth for DiddiGo: route
distance, duration, and place search. If DiddiMap is unavailable or returns an
unexpected payload, this adapter raises an ApiError. It must never fabricate a
silent fallback distance, duration, or geocode result.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

import httpx

from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.shared_kernel.contracts.routing import GeoPoint, RouteTracePoint
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


@dataclass(frozen=True)
class RouteTraceAnalysisResult:
    actual_distance_km: Decimal | None
    actual_duration_seconds: int | None
    usable_for_scoring: bool = True
    recommendation: str | None = None
    quality_label: str | None = None
    quality_score: Decimal | None = None
    points_count: int | None = None
    usable_points_count: int | None = None


@dataclass
class DiddiMapRoutingClient:
    base_url: str
    access_token: str | None = None
    service_client_id: str | None = None
    service_token: str | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url.rstrip("/"),
                timeout=self.timeout_seconds,
            )
        return self._client

    def _auth_headers(self) -> dict[str, str]:
        if self.service_token:
            headers = {"Authorization": f"Bearer {self.service_token}"}
            if self.service_client_id:
                headers["X-Client-ID"] = self.service_client_id
            return headers
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    def _trace_path(self, path: str) -> str:
        if self.service_token:
            return f"/api/v1/integrations/diddigo{path}"
        return f"/api/v1{path}"

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
        started = time.perf_counter()
        try:
            response = await self._http().post("/api/v1/route", json=request_payload)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.exception("DiddiMap route unavailable: %s", exc)
            log_event(
                "diddimap.request.failed",
                level="error",
                path="/api/v1/route",
                operation="route",
                duration_ms=_duration_ms(started),
                error=str(exc),
            )
            raise ApiError(503, "DIDDIMAP_UNAVAILABLE", "Service geographique indisponible.") from exc
        except ValueError as exc:
            logger.exception("DiddiMap route returned invalid JSON: %s", exc)
            log_event(
                "diddimap.request.failed",
                level="error",
                path="/api/v1/route",
                operation="route",
                duration_ms=_duration_ms(started),
                error="invalid_json",
            )
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Reponse geographique invalide.") from exc

        result = self._parse_route(payload)
        log_event(
            "diddimap.request.succeeded",
            path="/api/v1/route",
            operation="route",
            duration_ms=_duration_ms(started),
            distance_km=result.distance_km,
            duration_seconds=result.duration_seconds,
        )
        return result

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
        started = time.perf_counter()
        try:
            response = await self._http().get("/api/v1/geocoding/search", params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.exception("DiddiMap geocoding unavailable: %s", exc)
            log_event(
                "diddimap.request.failed",
                level="error",
                path="/api/v1/geocoding/search",
                operation="geocode",
                duration_ms=_duration_ms(started),
                error=str(exc),
            )
            raise ApiError(503, "DIDDIMAP_UNAVAILABLE", "Service geographique indisponible.") from exc
        except ValueError as exc:
            logger.exception("DiddiMap geocoding returned invalid JSON: %s", exc)
            log_event(
                "diddimap.request.failed",
                level="error",
                path="/api/v1/geocoding/search",
                operation="geocode",
                duration_ms=_duration_ms(started),
                error="invalid_json",
            )
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Reponse geographique invalide.") from exc

        results = self._parse_geocode(payload)
        log_event(
            "diddimap.request.succeeded",
            path="/api/v1/geocoding/search",
            operation="geocode",
            duration_ms=_duration_ms(started),
            results_count=len(results),
        )
        return results

    async def start_trace(
        self,
        *,
        start: GeoPoint,
        end: GeoPoint,
        planned_distance_km: Decimal | None,
        planned_duration_seconds: int | None,
        profile: str = DEFAULT_PROFILE,
        source_ride_id: str | None = None,
    ) -> str:
        payload = {
            "start": {"lng": start.lng, "lat": start.lat},
            "end": {"lng": end.lng, "lat": end.lat},
            "profile": _abidjanmaps_profile(profile),
            "source_ride_id": source_ride_id,
            "planned_distance_m": _km_to_meters(planned_distance_km),
            "planned_duration_s": planned_duration_seconds,
            "planned_route_geometry": {"type": "LineString", "coordinates": []},
        }
        payload = {key: value for key, value in payload.items() if value is not None}
        response_payload = await self._post_json(
            self._trace_path("/map-traces/start"),
            payload,
            unavailable_message="DiddiMap trace start unavailable",
        )
        trace_id = response_payload.get("id") if isinstance(response_payload, dict) else None
        if trace_id is None:
            logger.error("DiddiMap trace start returned unrecognised payload: %r", response_payload)
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Trace DiddiMap invalide.")
        return str(trace_id)

    async def append_trace_positions(self, trace_id: str, points: list[RouteTracePoint]) -> None:
        if not points:
            return
        payload = {
            "positions": [
                {
                    "lat": point.location.lat,
                    "lng": point.location.lng,
                    "accuracy_m": float(point.accuracy_m) if point.accuracy_m is not None else None,
                    "speed_mps": float(point.speed_kmh) / 3.6 if point.speed_kmh is not None else None,
                    "recorded_at": _iso(point.recorded_at),
                }
                for point in points
            ]
        }
        for position in payload["positions"]:
            for key in [key for key, value in position.items() if value is None]:
                del position[key]
        await self._post_json(
            self._trace_path(f"/map-traces/{trace_id}/positions"),
            payload,
            unavailable_message="DiddiMap trace positions unavailable",
            tolerated_conflict_codes={"trace_already_finished", "trace_not_accepting_positions"},
        )

    async def finish_trace(self, trace_id: str, *, finished_at: datetime) -> None:
        await self._post_json(
            self._trace_path(f"/map-traces/{trace_id}/finish"),
            {"finished_at": _iso(finished_at)},
            unavailable_message="DiddiMap trace finish unavailable",
            tolerated_conflict_codes={"trace_already_finished"},
        )

    async def analyze_trace(self, trace_id: str) -> RouteTraceAnalysisResult:
        payload = await self._post_json(
            self._trace_path(f"/map-traces/{trace_id}/analyze"),
            {},
            unavailable_message="DiddiMap trace analyze unavailable",
        )
        if not isinstance(payload, dict):
            logger.error("DiddiMap trace analyze returned non-object payload: %r", payload)
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Analyse DiddiMap invalide.")
        recommendation = _optional_string(payload.get("recommendation"))
        quality_label = _optional_string(payload.get("quality_label"))
        quality_score = _optional_decimal(payload.get("quality_score"))
        points_count = _optional_int(payload.get("points_count"))
        usable_points_count = _optional_int(payload.get("usable_points_count"))
        try:
            actual_distance_m = Decimal(str(payload["actual_distance_m"]))
            actual_duration_seconds = int(payload["actual_duration_s"])
        except (KeyError, TypeError, ValueError) as exc:
            logger.exception("DiddiMap trace analyze sent invalid metrics: %r", payload)
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Metriques DiddiMap invalides.") from exc
        if recommendation == "ignore_for_scoring":
            return RouteTraceAnalysisResult(
                actual_distance_km=None,
                actual_duration_seconds=None,
                usable_for_scoring=False,
                recommendation=recommendation,
                quality_label=quality_label,
                quality_score=quality_score,
                points_count=points_count,
                usable_points_count=usable_points_count,
            )
        if actual_distance_m <= 0 or actual_duration_seconds <= 0:
            logger.error("DiddiMap trace analyze sent unusable metrics: %r", payload)
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Metriques DiddiMap inutilisables.")
        return RouteTraceAnalysisResult(
            actual_distance_km=actual_distance_m / Decimal(1000),
            actual_duration_seconds=actual_duration_seconds,
            recommendation=recommendation,
            quality_label=quality_label,
            quality_score=quality_score,
            points_count=points_count,
            usable_points_count=usable_points_count,
        )

    async def _post_json(
        self,
        path: str,
        payload: dict,
        *,
        unavailable_message: str,
        tolerated_conflict_codes: set[str] | None = None,
    ) -> object:
        started = time.perf_counter()
        try:
            response = await self._http().post(path, json=payload, headers=self._auth_headers())
            response.raise_for_status()
            result = response.json()
            log_event(
                "diddimap.request.succeeded",
                path=path,
                operation=_operation_from_path(path),
                duration_ms=_duration_ms(started),
            )
            return result
        except httpx.HTTPStatusError as exc:
            provider_code = _provider_error_code(exc.response)
            if exc.response.status_code == 409 and provider_code in (tolerated_conflict_codes or set()):
                log_event(
                    "diddimap.request.conflict_tolerated",
                    level="warning",
                    path=path,
                    operation=_operation_from_path(path),
                    duration_ms=_duration_ms(started),
                    provider_code=provider_code,
                )
                return {"provider_code": provider_code, "idempotent": True}
            logger.warning("%s: status=%s code=%s", unavailable_message, exc.response.status_code, provider_code)
            log_event(
                "diddimap.request.rejected",
                level="warning",
                path=path,
                operation=_operation_from_path(path),
                duration_ms=_duration_ms(started),
                status_code=exc.response.status_code,
                provider_code=provider_code,
            )
            raise ApiError(
                exc.response.status_code,
                "DIDDIMAP_BUSINESS_ERROR",
                "DiddiMap a refuse l'operation.",
                {"provider_code": provider_code},
            ) from exc
        except httpx.RequestError as exc:
            logger.exception("%s: %s", unavailable_message, exc)
            log_event(
                "diddimap.request.failed",
                level="error",
                path=path,
                operation=_operation_from_path(path),
                duration_ms=_duration_ms(started),
                error=str(exc),
            )
            raise ApiError(503, "DIDDIMAP_UNAVAILABLE", "Service geographique indisponible.") from exc
        except ValueError as exc:
            logger.exception("DiddiMap returned invalid JSON for %s: %s", path, exc)
            log_event(
                "diddimap.request.failed",
                level="error",
                path=path,
                operation=_operation_from_path(path),
                duration_ms=_duration_ms(started),
                error="invalid_json",
            )
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Reponse geographique invalide.") from exc

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


def _provider_error_code(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    error = payload.get("error")
    if isinstance(error, dict) and isinstance(error.get("code"), str):
        return error["code"]
    detail = payload.get("detail")
    if isinstance(detail, dict) and isinstance(detail.get("code"), str):
        return detail["code"]
    code = payload.get("code")
    return code if isinstance(code, str) else None


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _abidjanmaps_profile(profile: str) -> str:
    if profile == DEFAULT_PROFILE:
        return "car"
    return profile


def _km_to_meters(distance_km: Decimal | None) -> int | None:
    if distance_km is None:
        return None
    return int(round(float(distance_km * Decimal(1000))))


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _duration_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _operation_from_path(path: str) -> str:
    if "map-traces" in path:
        return "trace"
    return path.strip("/").replace("/", ".")
