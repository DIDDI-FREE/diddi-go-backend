from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.scoring_service import ScoringService
from app_base.modules.ride.domain.entities import DriverProfile, DriverStatus, Ride, RideStatus

pytestmark = pytest.mark.unit


PASSENGER_ID = uuid4()
DRIVER_USER_ID = uuid4()
DRIVER_PROFILE_ID = uuid4()
OTHER_USER_ID = uuid4()
RIDE_ID = uuid4()


class FakeRideRepo:
    def __init__(self, ride: Ride | None = None) -> None:
        self.ride = ride

    async def find_by_id(self, ride_id: UUID) -> Ride | None:
        return self.ride if self.ride and ride_id == self.ride.id else None

    async def passenger_scoring_stats(self, passenger_user_id: UUID) -> dict:
        if passenger_user_id != PASSENGER_ID:
            return {}
        return {
            "total_rides": 8,
            "completed_rides": 7,
            "cancelled_rides": 1,
            "emergency_reports": 0,
            "rating_count": 4,
            "rating_avg": "4.75",
        }

    async def driver_scoring_stats(self, driver_id: UUID) -> dict:
        if driver_id != DRIVER_PROFILE_ID:
            return {}
        return {
            "total_rides": 12,
            "completed_rides": 11,
            "cancelled_rides": 1,
            "emergency_reports": 0,
            "rating_count": 9,
            "rating_avg": "4.80",
        }

    async def ride_rating_summary(self, ride_id: UUID) -> dict:
        if ride_id != RIDE_ID:
            return {}
        return {"rating_count": 2, "rating_avg": "4.50"}


class FakeDriverRepo:
    async def find_by_user_id(self, user_id: UUID) -> DriverProfile | None:
        if user_id != DRIVER_USER_ID:
            return None
        return DriverProfile(
            id=DRIVER_PROFILE_ID,
            user_id=DRIVER_USER_ID,
            license_number="CI-SCORE",
            status=DriverStatus.ACTIVE,
        )


def scoring_service(ride: Ride | None = None) -> ScoringService:
    return ScoringService(ride_repo=FakeRideRepo(ride), driver_repo=FakeDriverRepo())


def completed_ride() -> Ride:
    return Ride(
        id=RIDE_ID,
        passenger_user_id=PASSENGER_ID,
        status=RideStatus.COMPLETED,
        driver_id=DRIVER_PROFILE_ID,
    )


@pytest.mark.asyncio
async def test_my_scores_returns_passenger_score_and_null_driver_without_profile() -> None:
    result = await scoring_service().get_my_scores(PASSENGER_ID)

    assert result["service"] == "diddigo"
    assert result["passenger_score"]["subject_type"] == "passenger"
    assert result["passenger_score"]["score_value"] > 4
    assert result["driver_score"] is None


@pytest.mark.asyncio
async def test_my_scores_returns_driver_score_when_profile_exists() -> None:
    result = await scoring_service().get_my_scores(DRIVER_USER_ID)

    assert result["driver_score"]["subject_type"] == "driver"
    assert result["driver_score"]["subject_id"] == str(DRIVER_PROFILE_ID)
    assert result["driver_score"]["metrics"]["completed_rides"] == 11
    assert "good_ratings" in result["driver_score"]["reason_codes"]


@pytest.mark.asyncio
async def test_ride_score_requires_participant_or_admin() -> None:
    service = scoring_service(completed_ride())

    with pytest.raises(ApiError) as exc_info:
        await service.get_ride_score(RIDE_ID, actor_user_id=OTHER_USER_ID, actor_role="user")

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "RIDE_NOT_OWNED_BY_USER"


@pytest.mark.asyncio
async def test_completed_trip_score_uses_ratings_and_status() -> None:
    result = await scoring_service(completed_ride()).get_ride_score(
        RIDE_ID,
        actor_user_id=PASSENGER_ID,
        actor_role="user",
    )

    assert result["subject_type"] == "trip"
    assert result["score_status"] == "stable"
    assert result["metrics"]["ride_status"] == "completed"
    assert result["metrics"]["rating_avg"] == 4.5
    assert "status_completed" in result["reason_codes"]
