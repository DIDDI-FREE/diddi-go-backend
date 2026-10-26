from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app_base.core.database import async_session_factory, engine
from app_base.core.errors import ApiError
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.domain.entities import RideRating
from app_base.modules.ride.infra import models as orm
from app_base.modules.ride.infra.repositories import SqlAlchemyRideRepository


def _point() -> object:
    return from_shape(Point(-4.0161, 5.3204), srid=4326)


def _ride(
    *,
    ride_id: UUID,
    passenger_id: UUID,
    driver_id: UUID | None,
    status: str,
    emergency_status: str | None = None,
) -> orm.RideModel:
    now = datetime.now(UTC)
    return orm.RideModel(
        id=ride_id,
        passenger_user_id=passenger_id,
        driver_id=driver_id,
        status=status,
        pickup_location=_point(),
        dropoff_location=_point(),
        requested_at=now,
        emergency_status=emergency_status,
    )


@pytest.mark.asyncio
async def test_real_postgres_scoring_aggregations_use_only_actor_eligible_rides() -> None:
    passenger_id = uuid4()
    driver_user_id = uuid4()
    driver_id = uuid4()
    completed_id, passenger_cancel_id, driver_cancel_id, active_id, no_driver_id = [
        uuid4() for _ in range(5)
    ]

    async with async_session_factory() as session:
        session.add_all(
            [
                UserModel(
                    id=passenger_id,
                    phone=f"+225{passenger_id.int % 10_000_000_000:010d}",
                    role="passenger",
                ),
                UserModel(
                    id=driver_user_id,
                    phone=f"+225{driver_user_id.int % 10_000_000_000:010d}",
                    role="passenger",
                ),
                orm.DriverProfileModel(
                    id=driver_id,
                    user_id=driver_user_id,
                    license_number=f"LIC-{driver_id.hex[:12]}",
                    status="active",
                ),
                _ride(
                    ride_id=completed_id,
                    passenger_id=passenger_id,
                    driver_id=driver_id,
                    status="completed",
                ),
                _ride(
                    ride_id=passenger_cancel_id,
                    passenger_id=passenger_id,
                    driver_id=driver_id,
                    status="cancelled_by_passenger",
                ),
                _ride(
                    ride_id=driver_cancel_id,
                    passenger_id=passenger_id,
                    driver_id=driver_id,
                    status="cancelled_by_driver",
                ),
                _ride(
                    ride_id=active_id,
                    passenger_id=passenger_id,
                    driver_id=driver_id,
                    status="in_progress",
                    emergency_status="notified",
                ),
                _ride(ride_id=no_driver_id, passenger_id=passenger_id, driver_id=None, status="no_driver_found"),
                # Historical invalid ratings are retained but excluded because
                # their rides did not complete.
                orm.RideRatingModel(id=uuid4(), ride_id=completed_id, rater_role="passenger", rating=5),
                orm.RideRatingModel(id=uuid4(), ride_id=completed_id, rater_role="driver", rating=4),
                orm.RideRatingModel(id=uuid4(), ride_id=driver_cancel_id, rater_role="passenger", rating=1),
                orm.RideRatingModel(id=uuid4(), ride_id=passenger_cancel_id, rater_role="driver", rating=1),
            ]
        )
        await session.commit()

        repository = SqlAlchemyRideRepository(session)
        passenger = await repository.passenger_scoring_stats(passenger_id)
        driver = await repository.driver_scoring_stats(driver_id)
        public_rating = await repository.driver_rating_summary(driver_id)

    assert passenger == {
        "total_rides": 5,
        "eligible_rides": 2,
        "completed_rides": 1,
        "cancelled_rides": 1,
        "emergency_reports": 1,
        "rating_count": 1,
        "rating_avg": Decimal("4"),
    }
    assert driver == {
        "total_rides": 4,
        "eligible_rides": 2,
        "completed_rides": 1,
        "cancelled_rides": 1,
        "emergency_reports": 1,
        "rating_count": 1,
        "rating_avg": Decimal("5"),
    }
    assert public_rating == {"rating_count": 1, "rating_avg": Decimal("5")}
    # The application test client disposes this module-level pool after every
    # test. These direct database tests need the same Windows event-loop care.
    await engine.dispose()


@pytest.mark.asyncio
async def test_real_postgres_duplicate_rating_is_mapped_to_business_conflict() -> None:
    passenger_id, driver_user_id, driver_id, ride_id = uuid4(), uuid4(), uuid4(), uuid4()
    try:
        async with async_session_factory() as seed:
            seed.add_all(
                [
                UserModel(
                    id=passenger_id,
                    phone=f"+225{passenger_id.int % 10_000_000_000:010d}",
                    role="passenger",
                ),
                UserModel(
                    id=driver_user_id,
                    phone=f"+225{driver_user_id.int % 10_000_000_000:010d}",
                    role="passenger",
                ),
                orm.DriverProfileModel(
                    id=driver_id,
                    user_id=driver_user_id,
                    license_number=f"LIC-{driver_id.hex[:12]}",
                    status="active",
                ),
                _ride(
                    ride_id=ride_id,
                    passenger_id=passenger_id,
                    driver_id=driver_id,
                    status="completed",
                ),
                ]
            )
            await seed.commit()

        async with async_session_factory() as first_session:
            first = SqlAlchemyRideRepository(first_session)
            await first.save_rating(
                RideRating(id=uuid4(), ride_id=ride_id, rater_role="passenger", rating=5)
            )
            await first_session.commit()

        async with async_session_factory() as second_session:
            second = SqlAlchemyRideRepository(second_session)
            with pytest.raises(ApiError) as error:
                await second.save_rating(
                    RideRating(id=uuid4(), ride_id=ride_id, rater_role="passenger", rating=4)
                )

        assert error.value.status_code == 409
        assert error.value.code == "RATING_ALREADY_SUBMITTED"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_real_postgres_finds_latest_active_ride_for_passenger() -> None:
    passenger_id = uuid4()
    active_ride_id = uuid4()
    terminal_ride_id = uuid4()

    try:
        async with async_session_factory() as session:
            session.add(
                UserModel(
                    id=passenger_id,
                    phone=f"+225{passenger_id.int % 10_000_000_000:010d}",
                    role="passenger",
                )
            )
            session.add_all(
                [
                    _ride(
                        ride_id=terminal_ride_id,
                        passenger_id=passenger_id,
                        driver_id=None,
                        status="completed",
                    ),
                    _ride(
                        ride_id=active_ride_id,
                        passenger_id=passenger_id,
                        driver_id=None,
                        status="requested",
                    ),
                ]
            )
            await session.commit()

            repository = SqlAlchemyRideRepository(session)
            active_ride = await repository.find_active_by_passenger_user_id(passenger_id)

        assert active_ride is not None
        assert active_ride.id == active_ride_id
    finally:
        await engine.dispose()
