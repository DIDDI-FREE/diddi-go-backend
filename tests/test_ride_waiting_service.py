from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.domain.entities import DriverProfile, Ride, RideStatus


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


def waiting_service():
    user_id = uuid4()
    driver_id = uuid4()
    ride = Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        driver_id=driver_id,
        status=RideStatus.IN_PROGRESS,
        estimated_fare=Decimal("2500"),
    )
    profile = DriverProfile(id=driver_id, user_id=user_id, license_number="TEST")
    repo = FakeRideRepo(ride)
    service = RideService(
        ride_repo=repo,
        routing=None,
        pricing_rules=None,
        driver_repo=FakeDriverRepo(profile),
    )
    return service, repo, ride, user_id


@pytest.mark.asyncio
async def test_waiting_requires_recent_stationary_telemetry():
    service, _, ride, user_id = waiting_service()

    with pytest.raises(ApiError) as missing:
        await service.start_waiting(
            ride.id, actor_user_id=user_id, actor_role="driver", speed_kmh=None,
        )
    assert missing.value.code == "WAITING_TELEMETRY_REQUIRED"

    with pytest.raises(ApiError) as moving:
        await service.start_waiting(
            ride.id, actor_user_id=user_id, actor_role="driver", speed_kmh=12,
        )
    assert moving.value.code == "VEHICLE_NOT_STOPPED"


@pytest.mark.asyncio
async def test_waiting_start_and_stop_bills_each_started_minute():
    service, repo, ride, user_id = waiting_service()

    started = await service.start_waiting(
        ride.id, actor_user_id=user_id, actor_role="driver", speed_kmh=0,
    )
    assert started["status"] == "waiting"
    assert started["waiting"]["rate_per_minute"] == 100

    ride.waiting_started_at = datetime.now(UTC) - timedelta(seconds=61)
    stopped = await service.stop_waiting(
        ride.id, actor_user_id=user_id, actor_role="driver",
    )
    assert stopped["status"] == "in_progress"
    assert stopped["waiting"]["duration_seconds"] >= 61
    assert stopped["waiting"]["fee"] == 200
    assert repo.ride.status is RideStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_waiting_cannot_start_before_ride_is_in_progress():
    service, _, ride, user_id = waiting_service()
    ride.status = RideStatus.DRIVER_EN_ROUTE

    with pytest.raises(ApiError) as error:
        await service.start_waiting(
            ride.id, actor_user_id=user_id, actor_role="driver", speed_kmh=0,
        )
    assert error.value.code == "WAITING_INVALID_RIDE_STATUS"


@pytest.mark.asyncio
async def test_passenger_can_cancel_during_active_waiting():
    service, repo, ride, driver_user_id = waiting_service()
    await service.start_waiting(
        ride.id, actor_user_id=driver_user_id, actor_role="driver", speed_kmh=0,
    )
    ride.waiting_started_at = datetime.now(UTC) - timedelta(seconds=10)

    result = await service.cancel(
        ride.id,
        "passenger_changed_mind",
        actor_user_id=ride.passenger_user_id,
        actor_role="user",
    )

    assert result["status"] == "cancelled_by_passenger"
    assert repo.ride.status is RideStatus.CANCELLED_BY_PASSENGER
    assert repo.ride.waiting_started_at is None
    assert repo.ride.waiting_duration_seconds >= 10
    assert repo.ride.waiting_fee == Decimal("100")


@pytest.mark.asyncio
async def test_unrelated_user_cannot_cancel_ride():
    service, repo, ride, _ = waiting_service()

    with pytest.raises(ApiError) as error:
        await service.cancel(
            ride.id,
            "passenger_changed_mind",
            actor_user_id=uuid4(),
            actor_role="user",
        )

    assert error.value.code == "RIDE_NOT_OWNED_BY_USER"
    assert repo.ride.status is RideStatus.IN_PROGRESS
