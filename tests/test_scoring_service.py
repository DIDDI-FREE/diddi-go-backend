from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.scoring_service import ScoringService, _score_payload, _trip_score_payload
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
            "eligible_rides": 8,
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
            "eligible_rides": 12,
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


@pytest.mark.asyncio
async def test_internal_trip_score_reads_the_same_score_without_user_impersonation() -> None:
    result = await scoring_service(completed_ride()).get_ride_score_for_internal(RIDE_ID)

    assert result["ride_id"] == str(RIDE_ID)
    assert result["subject_type"] == "trip"
    assert result["score_status"] == "stable"


@pytest.mark.asyncio
async def test_internal_trip_score_returns_not_found_for_unknown_ride() -> None:
    with pytest.raises(ApiError) as exc_info:
        await scoring_service().get_ride_score_for_internal(RIDE_ID)

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "RIDE_NOT_FOUND"


def test_emergency_is_descriptive_but_never_changes_person_or_trip_score() -> None:
    baseline = {
        "total_rides": 4,
        "eligible_rides": 4,
        "completed_rides": 4,
        "cancelled_rides": 0,
        "rating_count": 2,
        "rating_avg": "4.50",
    }
    with_emergency = {**baseline, "emergency_reports": 3}

    assert _score_payload("passenger", baseline, subject_id=PASSENGER_ID)["score_value"] == _score_payload(
        "passenger", with_emergency, subject_id=PASSENGER_ID,
    )["score_value"]
    assert "emergency_reports" not in _score_payload(
        "passenger", with_emergency, subject_id=PASSENGER_ID,
    )["reason_codes"]

    ride = completed_ride()
    emergency_ride = completed_ride()
    emergency_ride.emergency_status = "notified"
    summary = {"rating_count": 1, "rating_avg": "4.00"}
    assert _trip_score_payload(ride, summary)["score_value"] == _trip_score_payload(
        emergency_ride, summary,
    )["score_value"]
    assert "emergency_reported" not in _trip_score_payload(emergency_ride, summary)["reason_codes"]


def test_new_user_keeps_neutral_score_but_is_explicitly_insufficient_data() -> None:
    result = _score_payload("passenger", {}, subject_id=PASSENGER_ID)

    assert result["score_value"] == 4.0
    assert result["score_status"] == "insufficient_data"
    assert result["score_level"] == "new"
    assert result["sample_size"] == 0
    assert result["metrics"]["rating_avg"] is None


def test_sample_size_counts_only_eligible_rides_not_ratings() -> None:
    result = _score_payload(
        "passenger",
        {
            "total_rides": 9,
            "eligible_rides": 2,
            "completed_rides": 2,
            "cancelled_rides": 0,
            "rating_count": 9,
            "rating_avg": "5.00",
        },
        subject_id=PASSENGER_ID,
    )

    assert result["sample_size"] == 2
    assert result["score_status"] == "insufficient_data"
