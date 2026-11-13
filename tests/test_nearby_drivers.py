from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app_base.core.auth_deps import get_current_active_user
from app_base.core.deps import nearby_drivers_service, user_repo
from app_base.main import app
from app_base.modules.ride.application.nearby_drivers import NearbyDriversService
from app_base.modules.ride.domain.entities import ComfortLevel, DriverStatus, VehicleCategory, VehicleVerificationStatus
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


@pytest.fixture
def preview():
    user_id = uuid4()
    profile = SimpleNamespace(id=uuid4(), status=DriverStatus.ACTIVE, is_review_account=False)
    vehicle = SimpleNamespace(
        category=VehicleCategory.STANDARD, comfort_level=ComfortLevel.PREMIUM,
        verification_status=VehicleVerificationStatus.ACTIVE,
    )
    service = NearbyDriversService(
        drivers=SimpleNamespace(find_by_user_id=AsyncMock(return_value=profile)),
        vehicles=SimpleNamespace(find_active_for_driver=AsyncMock(return_value=vehicle)),
        rides=SimpleNamespace(find_active_by_driver_user_id=AsyncMock(return_value=None)),
        locations=SimpleNamespace(
            find_available_nearby=AsyncMock(return_value=[user_id]),
            coordinates_for=AsyncMock(return_value={user_id: GeoPoint(lat=5.35991, lng=-4.00832)}),
        ),
        eligibility=SimpleNamespace(evaluate=AsyncMock(return_value={"eligible": True})),
    )
    return service, user_id, profile, vehicle


async def search(service, **overrides):
    args = dict(
        origin=GeoPoint(lat=5.36, lng=-4.01), radius_km=5, limit=20,
        vehicle_category=VehicleCategory.STANDARD, comfort_level=ComfortLevel.COMFORT,
        is_review_account=False,
    )
    return await service.search(**(args | overrides))


async def test_preview_returns_only_approximate_anonymous_markers(preview):
    service, user_id, _, _ = preview
    result = await search(service)
    assert result == {
        "drivers": [{
            "position": {"lat": 5.36, "lng": -4.008},
            "vehicle_category": "standard", "comfort_level": "premium",
        }],
        "radius_km": 5, "approximate": True,
    }
    assert str(user_id) not in str(result)
    service.locations.find_available_nearby.assert_awaited_once_with(
        GeoPoint(lat=5.36, lng=-4.01), radius_km=5, limit=100,
    )


@pytest.mark.parametrize("reason", [
    "missing_profile", "suspended", "review_cohort", "missing_vehicle", "category",
    "comfort", "occupied", "ineligible", "missing_position", "offline", "vehicle_unverified",
])
async def test_preview_excludes_unavailable_or_ineligible_drivers(preview, reason):
    service, _, profile, vehicle = preview
    if reason == "missing_profile":
        service.drivers.find_by_user_id.return_value = None
    elif reason == "suspended":
        profile.status = DriverStatus.SUSPENDED
    elif reason == "review_cohort":
        profile.is_review_account = True
    elif reason == "missing_vehicle":
        service.vehicles.find_active_for_driver.return_value = None
    elif reason == "category":
        vehicle.category = VehicleCategory.VAN
    elif reason == "vehicle_unverified":
        vehicle.verification_status = VehicleVerificationStatus.PENDING_VERIFICATION
    elif reason == "comfort":
        vehicle.comfort_level = ComfortLevel.STANDARD
    elif reason == "occupied":
        service.rides.find_active_by_driver_user_id.return_value = object()
    elif reason == "ineligible":
        service.eligibility.evaluate.return_value = {"eligible": False}
    elif reason == "missing_position":
        service.locations.coordinates_for.return_value = {}
    elif reason == "offline":
        service.locations.find_available_nearby.return_value = []
    assert (await search(service))["drivers"] == []


async def test_filtering_precedes_limit_and_preserves_nearest_order(preview):
    service, first, profile, _ = preview
    second, third = uuid4(), uuid4()
    service.locations.find_available_nearby.return_value = [first, second, third]
    service.locations.coordinates_for.return_value = {
        first: GeoPoint(lat=5.36, lng=-4.01),
        second: GeoPoint(lat=5.37, lng=-4.01),
        third: GeoPoint(lat=5.38, lng=-4.01),
    }
    service.drivers.find_by_user_id.side_effect = [None, profile, profile]
    result = await search(service, limit=1)
    assert [m["position"]["lat"] for m in result["drivers"]] == [5.37]
    assert service.drivers.find_by_user_id.await_count == 2


@pytest.fixture
def preview_client(preview):
    service, _, _, _ = preview
    previous = app.dependency_overrides.copy()
    app.dependency_overrides[nearby_drivers_service] = lambda: service
    app.dependency_overrides[get_current_active_user] = lambda: SimpleNamespace(is_review_account=False)
    try:
        yield TestClient(app), service
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)


def test_http_contract_and_no_cache(preview_client):
    client, _ = preview_client
    response = client.get("/v1/drivers/nearby?lat=5.36&lng=-4.01")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["drivers"][0]["position"] == {"lat": 5.36, "lng": -4.008}
    assert response.json()["approximate"] is True


@pytest.mark.parametrize("query", [
    "lat=86&lng=0", "lat=0&lng=181", "lat=nan&lng=0", "lat=0&lng=inf",
    "lat=0", "lat=0&lng=0&radius_km=0", "lat=0&lng=0&radius_km=11",
    "lat=0&lng=0&limit=0", "lat=0&lng=0&limit=51",
    "lat=0&lng=0&vehicle_category=boat", "lat=0&lng=0&comfort_level=unknown",
])
def test_http_rejects_invalid_search(preview_client, query):
    client, service = preview_client
    response = client.get("/v1/drivers/nearby?" + query)
    assert response.status_code == 422
    service.locations.find_available_nearby.assert_not_awaited()


def test_preview_requires_authentication():
    app.dependency_overrides[user_repo] = lambda: SimpleNamespace(find_by_id=AsyncMock())
    try:
        response = TestClient(app).get("/v1/drivers/nearby?lat=5.36&lng=-4.01")
    finally:
        app.dependency_overrides.pop(user_repo, None)
    assert response.status_code == 401


def test_openapi_exposes_typed_public_contract():
    operation = app.openapi()["paths"]["/v1/drivers/nearby"]["get"]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/NearbyDriversResponse",
    }
    assert operation["security"]
