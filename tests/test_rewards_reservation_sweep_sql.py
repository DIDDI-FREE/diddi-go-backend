"""Ticket 014: the sweep query on real Postgres, and one full sweep through the repositories."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app_base.core.database import async_session_factory, engine
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.payment.application.rewards_reservations import run_rewards_reservations_once
from app_base.modules.payment.infra import models as payment_orm
from app_base.modules.ride.infra import models as ride_orm
from app_base.modules.ride.infra.repositories import SqlAlchemyRideRepository


def _ride(passenger_id: UUID, *, status: str, rewards_status: str | None, requested_at: datetime, **extra):
    point = from_shape(Point(-4.0161, 5.3204), srid=4326)
    fields = {
        "id": uuid4(),
        "passenger_user_id": passenger_id,
        "status": status,
        "pickup_location": point,
        "dropoff_location": point,
        "estimated_fare": Decimal("1234"),
        "final_fare": Decimal("1234"),
        "currency": "XOF",
        "payment_method": "cash",
        "requested_at": requested_at,
        "rewards_reservation_id": uuid4() if rewards_status else None,
        "rewards_discount_amount": Decimal("246") if rewards_status else None,
        "rewards_status": rewards_status,
    }
    fields.update(extra)
    return ride_orm.RideModel(**fields)


class RecordingRewards:
    configured = True

    def __init__(self) -> None:
        self.confirms: list[dict] = []
        self.releases: list[dict] = []

    async def confirm(self, **kwargs) -> dict:
        self.confirms.append(kwargs)
        return {"consumption_id": str(uuid4())}

    async def release(self, **kwargs) -> dict:
        self.releases.append(kwargs)
        return {}


@pytest.mark.asyncio
async def test_sweep_closes_only_ended_rides_with_an_open_reservation() -> None:
    passenger_id = uuid4()
    now = datetime.now(UTC)
    recent = now - timedelta(minutes=10)
    paid = _ride(passenger_id, status="completed", rewards_status="reserved", requested_at=recent)
    unpaid = _ride(passenger_id, status="completed", rewards_status="reserved", requested_at=recent)
    cancelled = _ride(
        passenger_id, status="cancelled_by_passenger", rewards_status="release_deferred", requested_at=recent,
        cancellation_reason="changed_mind",
    )
    no_driver = _ride(passenger_id, status="no_driver_found", rewards_status="reserved", requested_at=recent)
    in_progress = _ride(passenger_id, status="in_progress", rewards_status="reserved", requested_at=recent)
    confirmed = _ride(passenger_id, status="completed", rewards_status="confirmed", requested_at=recent)
    released = _ride(passenger_id, status="cancelled_by_passenger", rewards_status="released", requested_at=recent)
    no_rewards = _ride(passenger_id, status="completed", rewards_status=None, requested_at=recent)
    too_old = _ride(
        passenger_id, status="no_driver_found", rewards_status="reserved", requested_at=now - timedelta(days=30)
    )
    rides = [paid, unpaid, cancelled, no_driver, in_progress, confirmed, released, no_rewards, too_old]
    ids = {name: ride.id for name, ride in zip(
        ["paid", "unpaid", "cancelled", "no_driver", "in_progress", "confirmed", "released", "no_rewards", "too_old"],
        rides, strict=True,
    )}

    async with async_session_factory() as session:
        session.add(UserModel(id=passenger_id, phone=f"+225{passenger_id.int % 10_000_000_000:010d}", role="user"))
        await session.flush()
        session.add_all(rides)
        await session.flush()
        session.add(
            payment_orm.TransactionModel(
                id=uuid4(), ride_id=ids["paid"], amount=Decimal("988"), method="cash", status="collected",
                collected_at=now, created_at=now,
            )
        )
        await session.commit()

        listed = await SqlAlchemyRideRepository(session).list_open_rewards_reservations(
            since=now - timedelta(days=7), limit=500
        )
    ours = {ride.id for ride in listed} & set(ids.values())
    assert ours == {ids["paid"], ids["unpaid"], ids["cancelled"], ids["no_driver"]}

    rewards = RecordingRewards()
    report = await run_rewards_reservations_once(rewards, limit=500)
    assert report["errors"] == 0

    confirmed_rides = {call["ride_id"] for call in rewards.confirms} & set(ids.values())
    released_reasons = {call["ride_id"]: call["reason"] for call in rewards.releases if call["ride_id"] in ours}
    assert confirmed_rides == {ids["paid"]}
    assert released_reasons == {ids["cancelled"]: "changed_mind", ids["no_driver"]: "no_driver_found"}

    async with async_session_factory() as session:
        statuses = {
            name: (await session.get(ride_orm.RideModel, ride_id)).rewards_status for name, ride_id in ids.items()
        }
    assert statuses["paid"] == "confirmed"
    assert statuses["unpaid"] == "reserved"
    assert statuses["cancelled"] == "released"
    assert statuses["no_driver"] == "released"
    assert statuses["in_progress"] == "reserved"
    assert statuses["too_old"] == "reserved"
    await engine.dispose()
