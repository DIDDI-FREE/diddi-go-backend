"""SCRUM-63 / UC-283 — weighted-ETA re-ranking of the dispatch shortlist.

The engine gathers a nearest-first eligible shortlist, then re-ranks it by real
DiddiMap ETA to the pickup, degrading to distance order whenever ETA is
unavailable so ranking never blocks dispatch.
"""

from dataclasses import dataclass
from uuid import uuid4

import pytest

from app_base.modules.ride.application.matching_service import MatchingService
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    DriverProfile,
    DriverStatus,
    Ride,
    RideStatus,
    Vehicle,
    VehicleCategory,
)
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


@dataclass
class _Estimate:
    distance_km: float
    duration_seconds: int


class FakeMultiDriverRepo:
    def __init__(self, profiles):
        self.by_user = {p.user_id: p for p in profiles}

    async def find_by_user_id(self, user_id):
        return self.by_user.get(user_id)


class FakeMultiVehicleRepo:
    def __init__(self, vehicles):
        self.by_driver = {v.driver_id: v for v in vehicles}

    async def find_active_for_driver(self, driver_id):
        vehicle = self.by_driver.get(driver_id)
        return vehicle if vehicle and vehicle.active else None


class FakeLocations:
    def __init__(self, ordered_user_ids, coords):
        self.ordered = ordered_user_ids
        self.coords = coords

    async def find_available_nearby(self, location, radius_km, limit=20):
        return self.ordered[:limit]

    async def coordinates_for(self, user_ids):
        return {u: self.coords[u] for u in user_ids if u in self.coords}


class FakeOffers:
    def __init__(self):
        self.current = set()
        self.tried = set()

    async def current_offers(self, ride_id):
        return set(self.current)

    async def already_tried(self, ride_id):
        return set(self.tried)

    async def open_offers(self, ride_id, driver_user_ids):
        self.current = set(driver_user_ids)
        self.tried.update(driver_user_ids)


class FakeRouting:
    def __init__(self, eta_by_origin, *, fail=False):
        self.eta_by_origin = eta_by_origin
        self.fail = fail

    async def estimate(self, origin, destination, profile):
        if self.fail:
            raise RuntimeError("DiddiMap unavailable")
        return _Estimate(distance_km=1.0, duration_seconds=self.eta_by_origin[(origin.lat, origin.lng)])


def _build(eta_seconds, *, routing_fail=False, with_routing=True, coords_present=None):
    """Three eligible drivers in distance order u0,u1,u2 with the given ETAs."""
    user_ids = [uuid4() for _ in range(3)]
    driver_ids = [uuid4() for _ in range(3)]
    profiles = [
        DriverProfile(id=d, user_id=u, license_number=f"CI-{i}", status=DriverStatus.ACTIVE)
        for i, (d, u) in enumerate(zip(driver_ids, user_ids, strict=True))
    ]
    vehicles = [
        Vehicle(id=uuid4(), driver_id=d, plate_number=f"CI-{i}",
                category=VehicleCategory.STANDARD, comfort_level=ComfortLevel.STANDARD)
        for i, d in enumerate(driver_ids)
    ]
    coords = {u: GeoPoint(lat=float(i), lng=0.0) for i, u in enumerate(user_ids)}
    if coords_present is not None:
        coords = {user_ids[i]: coords[user_ids[i]] for i in coords_present}
    eta_by_origin = {(float(i), 0.0): eta_seconds[i] for i in range(3) if i in (coords_present or range(3))}
    ride = Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        status=RideStatus.REQUESTED,
        pickup_location=GeoPoint(lat=5.35, lng=-4.0),
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.STANDARD,
    )
    service = MatchingService(
        ride_repo=None,
        driver_repo=FakeMultiDriverRepo(profiles),
        vehicle_repo=FakeMultiVehicleRepo(vehicles),
        locations=FakeLocations(user_ids, coords),
        offers=FakeOffers(),
        routing=FakeRouting(eta_by_origin, fail=routing_fail) if with_routing else None,
    )
    return service, ride, user_ids


@pytest.mark.asyncio
async def test_shortlist_is_reordered_by_eta_not_distance() -> None:
    # Distance order u0,u1,u2 but ETA makes u1 fastest, then u2, then u0.
    service, ride, u = _build(eta_seconds={0: 300, 1: 100, 2: 200})
    dispatch = await service.try_match(ride)
    assert dispatch.driver_user_ids == [u[1], u[2], u[0]]


@pytest.mark.asyncio
async def test_falls_back_to_distance_order_when_diddimap_is_down() -> None:
    service, ride, u = _build(eta_seconds={0: 300, 1: 100, 2: 200}, routing_fail=True)
    dispatch = await service.try_match(ride)
    assert dispatch.driver_user_ids == [u[0], u[1], u[2]]


@pytest.mark.asyncio
async def test_no_routing_keeps_distance_order() -> None:
    service, ride, u = _build(eta_seconds={0: 300, 1: 100, 2: 200}, with_routing=False)
    dispatch = await service.try_match(ride)
    assert dispatch.driver_user_ids == [u[0], u[1], u[2]]


@pytest.mark.asyncio
async def test_drivers_without_a_known_position_rank_after_timed_ones() -> None:
    # Only u0 and u2 have positions/ETA; u1 has none -> u1 tails, timed sorted by ETA.
    service, ride, u = _build(eta_seconds={0: 300, 2: 200}, coords_present=[0, 2])
    dispatch = await service.try_match(ride)
    assert dispatch.driver_user_ids == [u[2], u[0], u[1]]
