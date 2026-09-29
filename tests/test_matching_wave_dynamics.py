"""SCRUM-63 Phase 2 — wave search dynamics.

UC-280 radius widens per wave (capped), UC-282 the search abandons after a
wall-clock budget, UC-287 no wave is opened when no free driver is nearby.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app_base.core.settings import settings
from app_base.modules.ride.application.matching_service import (
    OFFER_WAVE_SIZE,
    SEARCH_RADIUS_KM,
    MatchingService,
)
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    Ride,
    RideStatus,
    VehicleCategory,
)
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


class FakeLocations:
    def __init__(self, candidates=None):
        self.candidates = candidates or []
        self.last_radius = None

    async def find_available_nearby(self, location, radius_km, limit=20):
        self.last_radius = radius_km
        return self.candidates[:limit]

    async def coordinates_for(self, user_ids):
        return {}


class FakeOffers:
    def __init__(self, tried=None):
        self.tried = set(tried or [])
        self.current = set()
        self.open_called = 0

    async def already_tried(self, ride_id):
        return set(self.tried)

    async def current_offers(self, ride_id):
        return set(self.current)

    async def open_offers(self, ride_id, driver_user_ids):
        self.open_called += 1
        self.current = set(driver_user_ids)
        self.tried.update(driver_user_ids)

    async def clear(self, ride_id):
        self.current.clear()


class FakeRideRepo:
    def __init__(self, ride):
        self.ride = ride

    async def find_by_id(self, ride_id):
        return self.ride

    async def save(self, ride):
        self.ride = ride
        return ride

    async def record_status_transition(self, transition):
        return None


def _ride(requested_at=None):
    return Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        status=RideStatus.REQUESTED,
        pickup_location=GeoPoint(lat=5.35, lng=-4.0),
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.STANDARD,
        requested_at=requested_at,
    )


@pytest.mark.asyncio
async def test_radius_widens_on_the_second_wave() -> None:
    # Five drivers already tried => wave_number 1 => one radius step wider.
    offers = FakeOffers(tried=[uuid4() for _ in range(OFFER_WAVE_SIZE)])
    locations = FakeLocations(candidates=[])
    service = MatchingService(
        ride_repo=None, driver_repo=None, vehicle_repo=None, locations=locations, offers=offers,
    )

    await service._next_candidates(_ride())

    assert locations.last_radius == SEARCH_RADIUS_KM + settings.matching_search_radius_step_km


@pytest.mark.asyncio
async def test_radius_is_capped_at_the_maximum() -> None:
    offers = FakeOffers(tried=[uuid4() for _ in range(OFFER_WAVE_SIZE * 10)])
    locations = FakeLocations(candidates=[])
    service = MatchingService(
        ride_repo=None, driver_repo=None, vehicle_repo=None, locations=locations, offers=offers,
    )

    await service._next_candidates(_ride())

    assert locations.last_radius == settings.matching_search_radius_max_km


@pytest.mark.asyncio
async def test_search_is_abandoned_after_the_time_budget() -> None:
    ride = _ride(requested_at=datetime.now(UTC) - timedelta(seconds=settings.matching_search_budget_seconds + 30))
    offers = FakeOffers()
    # Drivers ARE nearby, but the budget must win before any wave is opened.
    locations = FakeLocations(candidates=[uuid4()])
    service = MatchingService(
        ride_repo=FakeRideRepo(ride), driver_repo=None, vehicle_repo=None, locations=locations, offers=offers,
    )

    dispatch = await service.try_match(ride)

    assert dispatch.no_driver_found is True
    assert ride.status is RideStatus.NO_DRIVER_FOUND
    assert offers.open_called == 0


@pytest.mark.asyncio
async def test_no_wave_opened_when_no_driver_is_nearby() -> None:
    ride = _ride(requested_at=datetime.now(UTC))
    offers = FakeOffers()
    locations = FakeLocations(candidates=[])
    service = MatchingService(
        ride_repo=FakeRideRepo(ride), driver_repo=None, vehicle_repo=None, locations=locations, offers=offers,
    )

    dispatch = await service.try_match(ride)

    assert dispatch.no_driver_found is True
    assert ride.status is RideStatus.NO_DRIVER_FOUND
    assert offers.open_called == 0
