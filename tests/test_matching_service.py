from uuid import uuid4

import pytest

from app_base.modules.ride.application.matching_service import MatchingService
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    DriverProfile,
    DriverStatus,
    Ride,
    Vehicle,
    VehicleCategory,
)

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
