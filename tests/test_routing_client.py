"""Tests for the DiddiMap routing client: parsing and explicit failures.

These use a stubbed httpx transport, so no DiddiMap instance is required for
the unit tests. DiddiMap is the only geographic provider; failures must be
visible instead of silently inventing distance, duration, or search results.
"""

from __future__ import annotations

import json

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


# --- /route ----------------------------------------------------------------

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
async def test_geocode_does_not_send_unsupported_bias_param() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json={"results": []})

    await client_with(handler).geocode("Rue du Commerce", bias=ORIGIN)
    assert "bias" not in seen


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


# --- pricing integration ---------------------------------------------------

async def test_pricing_fails_when_diddimap_is_down(client, passenger_headers) -> None:
    """A ride estimate cannot invent distance/duration without DiddiMap."""
    body = {
        "pickup": {"lat": 5.3599, "lng": -4.0083},
        "dropoff": {"lat": 5.3167, "lng": -4.0333},
        "vehicle_category": "standard",
    }
    response = await client.post("/v1/rides/pricing/estimate", json=body, headers=passenger_headers)
    assert response.status_code == 503
    payload = response.json()
    assert payload["error"]["code"] == "DIDDIMAP_UNAVAILABLE"
