"""Tests for the DiddiMap routing client: parsing and explicit failures.

These use a stubbed httpx transport, so no DiddiMap instance is required for
the unit tests. DiddiMap is the only geographic provider; failures must be
visible instead of silently inventing distance, duration, or search results.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from urllib.parse import parse_qs

import httpx
import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.infra.routing_client import DiddiMapRoutingClient
from app_base.shared_kernel.types import GeoPoint

ORIGIN = GeoPoint(lat=5.3599, lng=-4.0083)
DESTINATION = GeoPoint(lat=5.3167, lng=-4.0333)


def client_with(handler) -> DiddiMapRoutingClient:
    """Build a client whose connection pool is a stubbed transport."""
    client = DiddiMapRoutingClient(base_url="http://diddimap.test")
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://diddimap.test",
    )
    return client


def authed_client_with(handler) -> DiddiMapRoutingClient:
    client = DiddiMapRoutingClient(base_url="http://diddimap.test", access_token="trace-token")
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://diddimap.test",
    )
    return client


def service_client_with(handler) -> DiddiMapRoutingClient:
    client = DiddiMapRoutingClient(
        base_url="http://diddimap.test",
        service_client_id="diddigo-staging",
        service_token="service-token",
    )
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://diddimap.test",
    )
    return client


def s2s_client_with(handler, *, legacy_token: str | None = None) -> DiddiMapRoutingClient:
    client = DiddiMapRoutingClient(
        base_url="http://diddimap.test",
        service_client_id="diddigo-staging",
        service_token=legacy_token,
        service_client_secret="client-secret",
        service_audience="diddimap",
        service_token_url="http://identity.test/identity/v1/auth/service/token",
    )
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://diddimap.test",
    )
    return client


# --- /route ----------------------------------------------------------------


@pytest.mark.unit
async def test_s2s_route_requests_scoped_token_and_caches_it() -> None:
    token_requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_requests
        if request.url.host == "identity.test":
            token_requests += 1
            form = parse_qs(request.content.decode())
            assert request.url.path == "/identity/v1/auth/service/token"
            assert request.headers["x-client-id"] == "diddigo-staging"
            assert form == {
                "grant_type": ["client_credentials"],
                "client_id": ["diddigo-staging"],
                "client_secret": ["client-secret"],
                "audience": ["diddimap"],
                "scope": ["diddimap:routes:read"],
            }
            return httpx.Response(200, json={"access_token": "short-lived-token", "expires_in": 600})
        assert request.headers["authorization"] == "Bearer short-lived-token"
        assert request.headers["x-client-id"] == "diddigo-staging"
        return httpx.Response(200, json={"distance_km": 8.4, "duration_seconds": 1140})

    client = s2s_client_with(handler)
    await client.estimate(ORIGIN, DESTINATION)
    await client.estimate(ORIGIN, DESTINATION)

    assert token_requests == 1


@pytest.mark.unit
async def test_s2s_tokens_are_cached_separately_by_scope() -> None:
    requested_scopes: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "identity.test":
            scope = parse_qs(request.content.decode())["scope"][0]
            requested_scopes.append(scope)
            return httpx.Response(200, json={"access_token": f"token-{scope}", "expires_in": 600})
        if request.url.path == "/api/v1/route":
            return httpx.Response(200, json={"distance_km": 1, "duration_seconds": 60})
        return httpx.Response(200, json={"results": []})

    client = s2s_client_with(handler)
    await client.estimate(ORIGIN, DESTINATION)
    await client.geocode("Plateau")
    await client.estimate(ORIGIN, DESTINATION)

    assert requested_scopes == ["diddimap:routes:read", "diddimap:places:read"]


@pytest.mark.unit
async def test_configured_s2s_failure_never_falls_back_to_legacy_token() -> None:
    diddimap_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal diddimap_called
        if request.url.host == "identity.test":
            return httpx.Response(401, json={"error": {"code": "INVALID_CLIENT"}})
        diddimap_called = True
        return httpx.Response(200, json={"distance_km": 1, "duration_seconds": 60})

    client = s2s_client_with(handler, legacy_token="must-not-be-used")
    with pytest.raises(ApiError) as exc_info:
        await client.estimate(ORIGIN, DESTINATION)

    assert exc_info.value.code == "DIDDIMAP_AUTHENTICATION_FAILED"
    assert diddimap_called is False

@pytest.mark.unit
async def test_estimate_parses_the_native_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/route"
        assert request.method == "POST"
        assert request.content
        return httpx.Response(200, json={"distance_km": 8.4, "duration_seconds": 1140})

    result = await client_with(handler).estimate(ORIGIN, DESTINATION)
    assert result.distance_km == 8.4
    assert result.duration_seconds == 1140
    assert result.is_usable


@pytest.mark.unit
async def test_estimate_parses_an_abidjanmaps_shape_and_ignores_price() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "status": "ok",
                "route": {"distance_m": 11876, "duration_s": 983},
                "price": {"amount": 3200, "currency": "XOF"},
            },
        )

    result = await client_with(handler).estimate(ORIGIN, DESTINATION)
    assert result.distance_km == pytest.approx(11.876)
    assert result.duration_seconds == 983


@pytest.mark.unit
async def test_estimate_parses_an_osrm_shape() -> None:
    """DiddiMap may proxy OSRM directly: meters and float seconds."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"routes": [{"distance": 8400.0, "duration": 1140.7}]})

    result = await client_with(handler).estimate(ORIGIN, DESTINATION)
    assert result.distance_km == pytest.approx(8.4)
    assert result.duration_seconds == 1140


@pytest.mark.unit
async def test_estimate_maps_the_vtc_profile_to_abidjanmaps_car_profile() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"distance_km": 1.0, "duration_seconds": 60})

    await client_with(handler).estimate(ORIGIN, DESTINATION)
    assert seen["profile"] == "car"
    assert seen["start"] == {"lat": 5.3599, "lng": -4.0083}
    assert seen["end"] == {"lat": 5.3167, "lng": -4.0333}


@pytest.mark.unit
@pytest.mark.parametrize(
    "handler",
    [
        pytest.param(
            lambda request: (_ for _ in ()).throw(httpx.ConnectError("refused")),
            id="connection-refused",
        ),
        pytest.param(
            lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("timeout")),
            id="timeout",
        ),
        pytest.param(lambda request: httpx.Response(503), id="service-unavailable"),
        pytest.param(lambda request: httpx.Response(200, text="not json"), id="invalid-json"),
        pytest.param(lambda request: httpx.Response(200, json={"unexpected": 1}), id="unknown-shape"),
        pytest.param(
            lambda request: httpx.Response(200, json={"distance_km": "far"}),
            id="unparseable-values",
        ),
    ],
)
async def test_estimate_fails_loudly_instead_of_falling_back(handler) -> None:
    """DiddiMap is the only geographic provider; failures are explicit."""
    with pytest.raises(ApiError) as exc_info:
        await client_with(handler).estimate(ORIGIN, DESTINATION)
    assert exc_info.value.status_code in {502, 503}
    assert exc_info.value.code in {"DIDDIMAP_INVALID_RESPONSE", "DIDDIMAP_UNAVAILABLE"}


# --- /geocode --------------------------------------------------------------

@pytest.mark.unit
async def test_geocode_parses_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/geocoding/search"
        assert request.url.params["q"] == "Plateau"
        return httpx.Response(
            200,
            json={"results": [{"label": "Plateau, Abidjan", "location": {"lat": 5.3167, "lng": -4.0333}}]},
        )

    results = await client_with(handler).geocode("Plateau")
    assert len(results) == 1
    assert results[0].label == "Plateau, Abidjan"
    assert results[0].point.lat == 5.3167


@pytest.mark.unit
async def test_geocode_accepts_a_bare_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"name": "Yopougon", "lat": 5.35, "lng": -4.08}])

    results = await client_with(handler).geocode("Yopougon")
    assert [r.label for r in results] == ["Yopougon"]


@pytest.mark.unit
async def test_geocode_sends_bias_coordinates_and_limit() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json={"results": []})

    await client_with(handler).geocode("Rue du Commerce", bias=ORIGIN, limit=7)
    assert seen["bias_lat"] == str(ORIGIN.lat)
    assert seen["bias_lng"] == str(ORIGIN.lng)
    assert seen["limit"] == "7"


@pytest.mark.unit
async def test_geocode_skips_malformed_entries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {"label": "Good", "location": {"lat": 5.3, "lng": -4.0}},
                    {"label": "Missing coords"},
                    "not-an-object",
                ]
            },
        )

    results = await client_with(handler).geocode("mixed")
    assert [r.label for r in results] == ["Good"]


@pytest.mark.unit
async def test_geocode_fails_loudly_when_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(ApiError) as exc_info:
        await client_with(handler).geocode("anything")
    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "DIDDIMAP_UNAVAILABLE"


# --- /map-traces -----------------------------------------------------------

@pytest.mark.unit
async def test_trace_start_uses_diddimap_contract_shape_and_auth() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/map-traces/start"
        assert request.headers["authorization"] == "Bearer trace-token"
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"id": 42, "status": "recording"})

    trace_id = await authed_client_with(handler).start_trace(
        start=ORIGIN,
        end=DESTINATION,
        planned_distance_km=Decimal("8.4"),
        planned_duration_seconds=1140,
        profile="palh_vtc",
    )

    assert trace_id == "42"
    assert seen == {
        "start": {"lng": -4.0083, "lat": 5.3599},
        "end": {"lng": -4.0333, "lat": 5.3167},
        "profile": "car",
        "planned_distance_m": 8400,
        "planned_duration_s": 1140,
        "planned_route_geometry": {"type": "LineString", "coordinates": []},
    }


@pytest.mark.unit
async def test_trace_start_uses_service_integration_contract_when_configured() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/integrations/diddigo/map-traces/start"
        assert request.headers["authorization"] == "Bearer service-token"
        assert request.headers["x-client-id"] == "diddigo-staging"
        seen.update(json.loads(request.content))
        return httpx.Response(200, json={"id": 42, "status": "recording"})

    trace_id = await service_client_with(handler).start_trace(
        start=ORIGIN,
        end=DESTINATION,
        planned_distance_km=Decimal("8.4"),
        planned_duration_seconds=1140,
        profile="palh_vtc",
        source_ride_id="ride-123",
    )

    assert trace_id == "42"
    assert seen["source_ride_id"] == "ride-123"
    assert seen["profile"] == "car"


@pytest.mark.unit
async def test_trace_request_propagates_bound_request_id() -> None:
    from app_base.core.observability import bind_request_id, reset_request_id

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-request-id"] == "req-trace-123"
        return httpx.Response(200, json={"id": 42, "status": "recording"})

    token = bind_request_id("req-trace-123")
    try:
        await service_client_with(handler).start_trace(
            start=ORIGIN,
            end=DESTINATION,
            planned_distance_km=Decimal("8.4"),
            planned_duration_seconds=1140,
            source_ride_id="ride-123",
        )
    finally:
        reset_request_id(token)


@pytest.mark.unit
async def test_trace_positions_convert_speed_to_meters_per_second() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/map-traces/42/positions"
        seen.update(json.loads(request.content))
        return httpx.Response(200, json=[])

    point = SimpleNamespace(
        location=ORIGIN,
        recorded_at=datetime(2026, 9, 3, 10, 5, tzinfo=UTC),
        speed_kmh=Decimal("36"),
        accuracy_m=Decimal("8"),
    )

    await authed_client_with(handler).append_trace_positions("42", [point])

    assert seen["positions"] == [
        {
            "lat": 5.3599,
            "lng": -4.0083,
            "accuracy_m": 8.0,
            "speed_mps": 10.0,
            "recorded_at": "2026-09-03T10:05:00Z",
        }
    ]


@pytest.mark.unit
async def test_trace_analyze_parses_actual_metrics() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/map-traces/42/analyze"
        return httpx.Response(200, json={"actual_distance_m": 12500, "actual_duration_s": 900})

    result = await authed_client_with(handler).analyze_trace("42")

    assert result.actual_distance_km == Decimal("12.5")
    assert result.actual_duration_seconds == 900
    assert result.usable_for_scoring is True


@pytest.mark.unit
async def test_trace_analyze_accepts_explicit_ignore_for_scoring() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "actual_distance_m": 0,
                "actual_duration_s": 1,
                "recommendation": "ignore_for_scoring",
                "quality_label": "weak",
                "quality_score": 0.48,
                "points_count": 2,
                "usable_points_count": 2,
            },
        )

    result = await authed_client_with(handler).analyze_trace("42")

    assert result.usable_for_scoring is False
    assert result.actual_distance_km is None
    assert result.actual_duration_seconds is None
    assert result.recommendation == "ignore_for_scoring"
    assert result.quality_label == "weak"
    assert result.points_count == 2


@pytest.mark.unit
async def test_trace_finish_tolerates_already_finished_conflict() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"error": {"code": "trace_already_finished"}})

    await authed_client_with(handler).finish_trace("42", finished_at=datetime.now(UTC))


@pytest.mark.unit
async def test_trace_business_conflict_is_not_reported_as_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"error": {"code": "trace_not_started"}})

    with pytest.raises(ApiError) as exc_info:
        await authed_client_with(handler).finish_trace("42", finished_at=datetime.now(UTC))

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "DIDDIMAP_BUSINESS_ERROR"
    assert exc_info.value.details == {"provider_code": "trace_not_started"}


@pytest.mark.unit
@pytest.mark.parametrize("provider_status", [401, 403])
async def test_trace_provider_auth_failure_is_not_exposed_as_user_auth_failure(provider_status: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(provider_status, json={"detail": "Unauthorized"})

    with pytest.raises(ApiError) as exc_info:
        await service_client_with(handler).finish_trace("42", finished_at=datetime.now(UTC))

    assert exc_info.value.status_code == 502
    assert exc_info.value.code == "DIDDIMAP_AUTHENTICATION_FAILED"
    assert exc_info.value.details["provider_status_code"] == provider_status


@pytest.mark.unit
async def test_trace_analyze_fails_loudly_on_unusable_metrics() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"actual_distance_m": 0, "actual_duration_s": 0})

    with pytest.raises(ApiError) as exc_info:
        await authed_client_with(handler).analyze_trace("42")

    assert exc_info.value.status_code == 502
    assert exc_info.value.code == "DIDDIMAP_INVALID_RESPONSE"


# --- pricing integration ---------------------------------------------------

async def test_pricing_fails_when_diddimap_is_down(client, passenger_headers) -> None:
    """A ride estimate cannot invent distance/duration without DiddiMap."""
    from app_base.main import app
    from app_base.modules.ride.infra.routing_client import DiddiMapRoutingClient

    previous_diddimap = app.state.diddimap
    app.state.diddimap = DiddiMapRoutingClient(base_url="http://127.0.0.1:9")
    body = {
        "pickup": {"lat": 5.3599, "lng": -4.0083},
        "dropoff": {"lat": 5.3167, "lng": -4.0333},
        "vehicle_category": "standard",
    }
    try:
        response = await client.post("/v1/rides/pricing/estimate", json=body, headers=passenger_headers)
        assert response.status_code == 503
        payload = response.json()
        assert payload["error"]["code"] == "DIDDIMAP_UNAVAILABLE"
    finally:
        app.state.diddimap = previous_diddimap
