from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.domain.entities import DriverProfile, DriverStatus, Ride, RideStatus

pytestmark = pytest.mark.unit


PASSENGER_ID = uuid4()
DRIVER_USER_ID = uuid4()
DRIVER_PROFILE_ID = uuid4()
OTHER_USER_ID = uuid4()
RIDE_ID = uuid4()


class FakeRideRepo:
    def __init__(self, ride: Ride) -> None:
        self.ride = ride
        self.last_list_filters: dict | None = None

    async def find_by_id(self, ride_id: UUID) -> Ride | None:
        return self.ride if ride_id == self.ride.id else None

    async def list_by(self, **filters):
        self.last_list_filters = filters
        if filters.get("driver_id") == self.ride.driver_id:
            return [self.ride], 1
        if filters.get("passenger_user_id") == self.ride.passenger_user_id:
            return [self.ride], 1
        return [], 0


class FakeDriverRepo:
    async def find_by_user_id(self, user_id: UUID) -> DriverProfile | None:
        if user_id != DRIVER_USER_ID:
            return None
        return DriverProfile(
            id=DRIVER_PROFILE_ID,
            user_id=DRIVER_USER_ID,
            license_number="CI-BUSINESS",
            status=DriverStatus.ACTIVE,
        )

    async def find_by_id(self, profile_id: UUID) -> DriverProfile | None:
        if profile_id != DRIVER_PROFILE_ID:
            return None
        return DriverProfile(
            id=DRIVER_PROFILE_ID,
            user_id=DRIVER_USER_ID,
            license_number="CI-BUSINESS",
            status=DriverStatus.ACTIVE,
        )


def service_with(ride: Ride) -> RideService:
    return RideService(
        ride_repo=FakeRideRepo(ride),
        routing=None,
        pricing_rules=None,
        driver_repo=FakeDriverRepo(),
    )


def matched_ride() -> Ride:
    return Ride(
        id=RIDE_ID,
        passenger_user_id=PASSENGER_ID,
        status=RideStatus.MATCHED,
        driver_id=DRIVER_PROFILE_ID,
    )


@pytest.mark.asyncio
async def test_business_driver_user_can_read_assigned_ride_detail() -> None:
    result = await service_with(matched_ride()).get_ride(
        RIDE_ID,
        actor_user_id=DRIVER_USER_ID,
        actor_role="passenger",
    )

    assert result["id"] == str(RIDE_ID)
    assert result["status"] == "matched"


@pytest.mark.asyncio
async def test_unassigned_user_cannot_read_someone_elses_ride_detail() -> None:
    with pytest.raises(ApiError) as exc_info:
        await service_with(matched_ride()).get_ride(
            RIDE_ID,
            actor_user_id=OTHER_USER_ID,
            actor_role="passenger",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "RIDE_NOT_OWNED_BY_USER"


@pytest.mark.asyncio
async def test_business_driver_user_role_lists_assigned_driver_rides() -> None:
    service = service_with(matched_ride())

    result = await service.list_rides(
        actor_user_id=DRIVER_USER_ID,
        actor_role="driver",
        page=1,
        page_size=20,
    )

    assert result["pagination"]["total_items"] == 1
    assert result["data"][0]["id"] == str(RIDE_ID)
    assert service.ride_repo.last_list_filters["driver_id"] == DRIVER_PROFILE_ID
