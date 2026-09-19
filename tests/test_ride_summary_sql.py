"""PostgreSQL contract for daily ride aggregates."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app_base.core.database import async_session_factory, engine
from app_base.modules.ride.infra.summary_repository import SqlAlchemyRideSummaryRepository


@pytest.mark.asyncio
async def test_summary_separates_request_and_completion_days(database) -> None:
    passenger_id = uuid4()
    rows = [
        ("completed", "2001-09-18T23:59:59+00:00", "2001-09-19T00:00:00+00:00", 2000),
        ("completed", "2001-09-19T12:00:00+00:00", "2001-09-19T12:30:00+00:00", 3000),
        ("cancelled_by_passenger", "2001-09-19T13:00:00+00:00", None, None),
        ("completed", "2001-09-19T16:00:00+00:00", "2001-09-19T17:00:00+00:00", None),
        ("completed", "2001-09-20T00:00:00+00:00", "2001-09-20T01:00:00+00:00", 4000),
    ]
    async with async_session_factory() as session:
        await session.execute(
            text("INSERT INTO auth.users (id, phone, role, status) VALUES (:id, :phone, 'passenger', 'active')"),
            {"id": passenger_id, "phone": "+2250700000099"},
        )
        for status, requested_at, completed_at, final_fare in rows:
            await session.execute(
                text(
                    "INSERT INTO ride.rides (id, passenger_user_id, status, comfort_level, "
                    "pickup_location, dropoff_location, requested_at, completed_at, final_fare, "
                    "currency, surge_multiplier, surge_cap, commission_rate, payment_method) "
                    "VALUES (:id, :passenger_id, :status, 'standard', "
                    "ST_GeomFromText('POINT(-4 5)', 4326)::geography, "
                    "ST_GeomFromText('POINT(-4.1 5.1)', 4326)::geography, "
                    ":requested_at, :completed_at, :final_fare, 'XOF', 1, 1.6, 0.08, 'cash')"
                ),
                {
                    "id": uuid4(),
                    "passenger_id": passenger_id,
                    "status": status,
                    "requested_at": datetime.fromisoformat(requested_at),
                    "completed_at": datetime.fromisoformat(completed_at) if completed_at else None,
                    "final_fare": final_fare,
                },
            )
        await session.commit()

        summary = await SqlAlchemyRideSummaryRepository(session).summarize_period(
            datetime(2001, 9, 19, tzinfo=UTC),
            datetime(2001, 9, 20, tzinfo=UTC),
        )

    try:
        assert summary.rides_requested == 3
        assert summary.rides_completed == 3
        assert summary.completed_fare_total_xof == Decimal("5000")
        assert summary.completed_rides_without_fare == 1
    finally:
        await engine.dispose()
