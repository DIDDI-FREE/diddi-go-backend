from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.services import RideService, _ride_start_code
from app_base.modules.ride.domain.entities import DriverProfile, Ride, RideStatus
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


class FakeRideRepo:
    def __init__(self, ride: Ride) -> None:
        self.ride = ride
        self.transitions = []

    async def find_by_id(self, ride_id):
        return self.ride if self.ride.id == ride_id else None

    async def save(self, ride):
        self.ride = ride
        return ride

    async def record_status_transition(self, transition):
        self.transitions.append(transition)


class FakeDriverRepo:
    def __init__(self, profile: DriverProfile) -> None:
        self.profile = profile

    async def find_by_user_id(self, user_id):
        return self.profile if self.profile.user_id == user_id else None


class FakeRouting:
    async def start_trace(self, **_kwargs):
        return "trace-1"


def departure_service():
    driver_user_id = uuid4()
    driver_id = uuid4()
    pickup = GeoPoint(lat=5.3525, lng=-3.9975)
    ride = Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        driver_id=driver_id,
        status=RideStatus.DRIVER_EN_ROUTE,
        pickup_location=pickup,
        dropoff_location=GeoPoint(lat=5.36, lng=-4.01),
        estimated_fare=Decimal("2500"),
    )
    repo = FakeRideRepo(ride)
    service = RideService(
        ride_repo=repo,
        routing=FakeRouting(),
        pricing_rules=None,
        driver_repo=FakeDriverRepo(DriverProfile(id=driver_id, user_id=driver_user_id, license_number="TEST")),
    )
    return service, repo, ride, driver_user_id, pickup


@pytest.mark.asyncio
async def test_arrival_requires_driver_inside_configured_radius():
    service, _, ride, user_id, _ = departure_service()
    with pytest.raises(ApiError) as error:
        await service.mark_arrived(
            ride.id,
            actor_user_id=user_id,
            actor_role="driver",
            driver_position=GeoPoint(lat=5.36, lng=-4.01),
        )
    assert error.value.code == "DRIVER_TOO_FAR_FROM_PICKUP"


@pytest.mark.asyncio
async def test_start_code_is_single_use_and_bills_only_after_free_wait():
    service, repo, ride, user_id, pickup = departure_service()
    await service.mark_arrived(
        ride.id,
        actor_user_id=user_id,
        actor_role="driver",
        driver_position=pickup,
    )
    ride.pre_ride_wait_started_at = datetime.now(UTC) - timedelta(seconds=240)

    result = await service.start_ride_with_code(
        ride.id,
        actor_user_id=user_id,
        actor_role="driver",
        code=_ride_start_code(ride.id),
    )

    assert result["status"] == "in_progress"
    assert repo.ride.pre_ride_wait_seconds >= 240
    assert repo.ride.pre_ride_wait_fee == Decimal("100")
    with pytest.raises(ApiError) as reused:
        await service.start_ride_with_code(
            ride.id,
            actor_user_id=user_id,
            actor_role="driver",
            code=_ride_start_code(ride.id),
        )
    assert reused.value.code == "RIDE_START_INVALID_STATUS"
