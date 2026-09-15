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


class FakeDriverRepo:
    def __init__(self, profile: DriverProfile) -> None:
        self.profile = profile

    async def find_by_user_id(self, user_id):
        return self.profile if self.profile.user_id == user_id else None


class FakeVehicleRepo:
    def __init__(self, vehicle: Vehicle) -> None:
        self.vehicle = vehicle

    async def find_active_for_driver(self, driver_id):
        return self.vehicle if self.vehicle.driver_id == driver_id and self.vehicle.active else None


class FakeMultiDriverRepo:
    def __init__(self, profiles: list[DriverProfile]) -> None:
        self.profiles_by_user = {profile.user_id: profile for profile in profiles}

    async def find_by_user_id(self, user_id):
        return self.profiles_by_user.get(user_id)


class FakeMultiVehicleRepo:
    def __init__(self, vehicles: list[Vehicle]) -> None:
        self.vehicles_by_driver = {vehicle.driver_id: vehicle for vehicle in vehicles}

    async def find_active_for_driver(self, driver_id):
        vehicle = self.vehicles_by_driver.get(driver_id)
        return vehicle if vehicle and vehicle.active else None


class FakeLocations:
    def __init__(self, candidates: list) -> None:
        self.candidates = candidates

    async def find_available_nearby(self, location, radius_km: float, limit: int = 20):
        return self.candidates[:limit]

    async def set_available(self, driver_id, *, available: bool) -> None:
        return None


class FakeOffers:
    def __init__(self) -> None:
        self.current: set = set()
        self.tried: set = set()

    async def open_offers(self, ride_id, driver_user_ids: list) -> None:
        self.current = set(driver_user_ids)
        self.tried.update(driver_user_ids)

    async def current_offers(self, ride_id):
        return set(self.current)

    async def decline_offer(self, ride_id, driver_user_id) -> bool:
        self.current.discard(driver_user_id)
        return bool(self.current)

    async def close_offer(self, ride_id) -> None:
        self.current.clear()

    async def already_tried(self, ride_id):
        return set(self.tried)

    async def claim(self, ride_id, driver_user_id) -> bool:
        return True

    async def release_claim(self, ride_id) -> None:
        return None

    async def clear(self, ride_id) -> None:
        self.current.clear()
        self.tried.clear()


class FakeRideRepo:
    def __init__(self, ride: Ride) -> None:
        self.ride = ride

    async def find_by_id(self, ride_id):
        return self.ride if ride_id == self.ride.id else None

    async def save(self, ride: Ride) -> Ride:
        self.ride = ride
        return ride

    async def record_status_transition(self, transition) -> None:
        return None


def _wave_service(candidate_count: int = 6) -> tuple[MatchingService, Ride, list]:
    user_ids = [uuid4() for _ in range(candidate_count)]
    driver_ids = [uuid4() for _ in range(candidate_count)]
    profiles = [
        DriverProfile(id=driver_id, user_id=user_id, license_number=f"CI-{index}", status=DriverStatus.ACTIVE)
        for index, (driver_id, user_id) in enumerate(zip(driver_ids, user_ids, strict=True))
    ]
    vehicles = [
        Vehicle(
            id=uuid4(),
            driver_id=driver_id,
            plate_number=f"CI-{index}",
            category=VehicleCategory.STANDARD,
            comfort_level=ComfortLevel.STANDARD,
        )
        for index, driver_id in enumerate(driver_ids)
    ]
    ride = Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        status=RideStatus.REQUESTED,
        pickup_location=GeoPoint(lat=5.3599, lng=-4.0083),
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.STANDARD,
    )
    service = MatchingService(
        ride_repo=FakeRideRepo(ride),
        driver_repo=FakeMultiDriverRepo(profiles),
        vehicle_repo=FakeMultiVehicleRepo(vehicles),
        locations=FakeLocations(user_ids),
        offers=FakeOffers(),
    )
    return service, ride, user_ids


@pytest.mark.asyncio
async def test_matching_rejects_vehicle_below_requested_comfort_level() -> None:
    driver_user_id = uuid4()
    driver_id = uuid4()
    service = MatchingService(
        ride_repo=None,
        driver_repo=FakeDriverRepo(
            DriverProfile(id=driver_id, user_id=driver_user_id, license_number="CI-123", status=DriverStatus.ACTIVE)
        ),
        vehicle_repo=FakeVehicleRepo(
            Vehicle(
                id=uuid4(),
                driver_id=driver_id,
                plate_number="CI-123-AA",
                category=VehicleCategory.STANDARD,
                comfort_level=ComfortLevel.STANDARD,
            )
        ),
        locations=None,
        offers=None,
    )
    ride = Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.PREMIUM,
    )

    can_take, reason = await service._can_take_ride(driver_user_id, ride)

    assert can_take is False
    assert reason == "comfort_level_mismatch:standard<premium"


@pytest.mark.asyncio
async def test_matching_accepts_vehicle_above_requested_comfort_level() -> None:
    driver_user_id = uuid4()
    driver_id = uuid4()
    service = MatchingService(
        ride_repo=None,
        driver_repo=FakeDriverRepo(
            DriverProfile(id=driver_id, user_id=driver_user_id, license_number="CI-123", status=DriverStatus.ACTIVE)
        ),
        vehicle_repo=FakeVehicleRepo(
            Vehicle(
                id=uuid4(),
                driver_id=driver_id,
                plate_number="CI-123-AA",
                category=VehicleCategory.STANDARD,
                comfort_level=ComfortLevel.PREMIUM,
            )
        ),
        locations=None,
        offers=None,
    )
    ride = Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.COMFORT,
    )

    can_take, reason = await service._can_take_ride(driver_user_id, ride)

    assert can_take is True
    assert reason is None


@pytest.mark.asyncio
async def test_try_match_opens_a_wave_of_five_drivers() -> None:
    service, ride, user_ids = _wave_service(candidate_count=6)

    dispatch = await service.try_match(ride)

    assert dispatch.new_wave is True
    assert dispatch.driver_user_ids == user_ids[:5]
    assert set(await service.offers.current_offers(ride.id)) == set(user_ids[:5])
    assert user_ids[5] not in await service.offers.current_offers(ride.id)


@pytest.mark.asyncio
async def test_decline_keeps_wave_open_until_all_wave_drivers_decline() -> None:
    service, ride, user_ids = _wave_service(candidate_count=6)
    await service.try_match(ride)

    dispatch = await service.decline(ride.id, user_ids[0])

    assert dispatch.new_wave is False
    assert set(dispatch.driver_user_ids) == set(user_ids[1:5])
    assert user_ids[5] not in dispatch.driver_user_ids


@pytest.mark.asyncio
async def test_expired_wave_advances_to_next_untried_driver() -> None:
    service, ride, user_ids = _wave_service(candidate_count=6)
    await service.try_match(ride)
    await service.offers.close_offer(ride.id)

    dispatch = await service.advance_expired_offer(ride.id)

    assert dispatch.new_wave is True
    assert dispatch.driver_user_ids == [user_ids[5]]
