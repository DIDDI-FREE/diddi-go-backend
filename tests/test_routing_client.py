"""Tests for the DiddiMap routing client — response parsing and the
degrade-don't-crash failure policy.

These use a stubbed httpx transport, so no DiddiMap instance is required.
"""

from __future__ import annotations

import httpx
import pytest

from app_base.modules.ride.infra.routing_client import (
    DiddiMapRoutingClient,
    RouteEstimateResult,
)
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


# --- /route ----------------------------------------------------------------

async def test_estimate_parses_the_native_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/route"
        assert request.url.params["profile"] == "palh_vtc"
        return httpx.Response(200, json={"distance_km": 8.4, "duration_seconds": 1140})

    result = await client_with(handler).estimate(ORIGIN, DESTINATION)
    assert result.distance_km == 8.4
    assert result.duration_seconds == 1140
    assert result.is_usable


async def test_estimate_parses_an_osrm_shape() -> None:
    """DiddiMap may proxy OSRM directly — meters and float seconds."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"routes": [{"distance": 8400.0, "duration": 1140.7}]})

    result = await client_with(handler).estimate(ORIGIN, DESTINATION)
    assert result.distance_km == pytest.approx(8.4)
    assert result.duration_seconds == 1140


async def test_estimate_sends_the_vtc_profile_by_default() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json={"distance_km": 1.0, "duration_seconds": 60})

    await client_with(handler).estimate(ORIGIN, DESTINATION)
    assert seen["profile"] == "palh_vtc"
    assert seen["origin"] == "5.3599,-4.0083"
    assert seen["destination"] == "5.3167,-4.0333"


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
            lambda request: httpx.Response(200, json={"distance_km": "far"}), id="unparseable-values",
        ),
    ],
)
async def test_estimate_degrades_instead_of_raising(handler) -> None:
    """Every transport or parsing failure must yield an unusable estimate
    rather than propagate — pricing then falls back to its own formula."""
    result = await client_with(handler).estimate(ORIGIN, DESTINATION)
    assert result == RouteEstimateResult(distance_km=0.0, duration_seconds=0)
    assert not result.is_usable


# --- /geocode --------------------------------------------------------------

async def test_geocode_parses_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/geocode"
        assert request.url.params["q"] == "Plateau"
        return httpx.Response(
            200,
            json={"results": [{"label": "Plateau, Abidjan", "lat": 5.3167, "lng": -4.0333}]},
        )

    results = await client_with(handler).geocode("Plateau")
    assert len(results) == 1
    assert results[0].label == "Plateau, Abidjan"
    assert results[0].point.lat == 5.3167


async def test_geocode_accepts_a_bare_list() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"name": "Yopougon", "lat": 5.35, "lng": -4.08}])

    results = await client_with(handler).geocode("Yopougon")
    assert [r.label for r in results] == ["Yopougon"]


async def test_geocode_passes_the_bias_point() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json={"results": []})

    await client_with(handler).geocode("Rue du Commerce", bias=ORIGIN)
    assert seen["bias"] == "5.3599,-4.0083"


async def test_geocode_skips_malformed_entries() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {"label": "Good", "lat": 5.3, "lng": -4.0},
                    {"label": "Missing coords"},
                    "not-an-object",
                ]
            },
        )

    results = await client_with(handler).geocode("mixed")
    assert [r.label for r in results] == ["Good"]


async def test_geocode_returns_empty_when_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    assert await client_with(handler).geocode("anything") == []


# --- pricing integration ---------------------------------------------------

async def test_pricing_still_works_when_diddimap_is_down(client, passenger_headers) -> None:
    """The whole point of the fallback: an unreachable DiddiMap (the default
    in local dev) must not stop a passenger getting a fare estimate."""
    body = {
        "pickup": {"lat": 5.3599, "lng": -4.0083},
        "dropoff": {"lat": 5.3167, "lng": -4.0333},
        "vehicle_category": "standard",
    }
    response = await client.post("/v1/rides/pricing/estimate", json=body, headers=passenger_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["distance_km"] > 0, "haversine fallback should produce a real distance"
    assert payload["estimated_fare"] > 0
