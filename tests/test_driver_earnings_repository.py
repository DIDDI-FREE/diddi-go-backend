from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app_base.core.database import async_session_factory, engine
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.payment.infra import models as payment_orm
from app_base.modules.payment.infra.repositories import SqlAlchemyPaymentRepository
from app_base.modules.ride.infra import models as ride_orm


def _point() -> object:
    return from_shape(Point(-4.0161, 5.3204), srid=4326)


@pytest.mark.asyncio
async def test_real_postgres_driver_earnings_include_cash_and_digital_settlements() -> None:
    passenger_id, driver_user_id, driver_id = uuid4(), uuid4(), uuid4()
    cash_ride_id, digital_ride_id, pending_ride_id = uuid4(), uuid4(), uuid4()
    settled_at = datetime(2026, 10, 2, 12, tzinfo=UTC)

    async with async_session_factory() as session:
        session.add_all(
            [
                UserModel(id=passenger_id, phone=f"+225{passenger_id.int % 10_000_000_000:010d}", role="user"),
                UserModel(id=driver_user_id, phone=f"+225{driver_user_id.int % 10_000_000_000:010d}", role="user"),
                ride_orm.DriverProfileModel(
                    id=driver_id,
                    user_id=driver_user_id,
                    license_number=f"LIC-{driver_id.hex[:12]}",
                    status="active",
                ),
                payment_orm.DriverWalletModel(id=uuid4(), driver_id=driver_id, balance=Decimal("4200")),
                _ride(cash_ride_id, passenger_id, driver_id, Decimal("8000"), Decimal("2000"), settled_at),
                _ride(digital_ride_id, passenger_id, driver_id, Decimal("4000"), Decimal("1000"), settled_at),
                _ride(pending_ride_id, passenger_id, driver_id, Decimal("7000"), Decimal("1750"), settled_at),
                payment_orm.TransactionModel(
                    id=uuid4(), ride_id=cash_ride_id, amount=Decimal("10000"), method="cash", status="collected",
                    collected_at=settled_at, created_at=settled_at,
                ),
                payment_orm.TransactionModel(
                    id=uuid4(),
                    ride_id=digital_ride_id,
                    amount=Decimal("5000"),
                    method="mobile_money",
                    status="succeeded",
                    paid_at=settled_at, created_at=settled_at,
                ),
                payment_orm.TransactionModel(
                    id=uuid4(),
                    ride_id=pending_ride_id,
                    amount=Decimal("8750"),
                    method="mobile_money",
                    status="pending",
                    created_at=settled_at,
                ),
                payment_orm.DriverWithdrawalModel(
                    id=uuid4(), driver_id=driver_id, quote_id=uuid4(), amount=Decimal("3000"), fees=Decimal("0"),
                    net_amount=Decimal("3000"), beneficiary_reference="driver:test", status="succeeded",
                    business_reference="test:withdrawal", idempotency_key="test:withdrawal:1", created_at=settled_at,
                    reserved_at=settled_at, succeeded_at=settled_at, updated_at=settled_at,
                ),
            ]
        )
        await session.commit()

        result = await SqlAlchemyPaymentRepository(session).summarize_driver_earnings(
            driver_id,
            period="day",
            start=datetime(2026, 10, 2, tzinfo=UTC),
            end=datetime(2026, 10, 3, tzinfo=UTC),
        )

    assert len(result) == 1
    bucket = result[0]
    assert bucket.ride_earnings == Decimal("12000")
    assert bucket.platform_commissions == Decimal("3000")
    assert bucket.pending_or_disputed == Decimal("7000")
    assert bucket.withdrawals_succeeded == Decimal("3000")
    await engine.dispose()


@pytest.mark.asyncio
async def test_driver_earnings_endpoint_returns_typed_summary_for_authenticated_driver(client, driver) -> None:
    wallet = (await client.get("/v1/drivers/me/wallet", headers=driver)).json()
    driver_id = UUID(wallet["driver_id"])
    passenger_id, ride_id = uuid4(), uuid4()
    settled_at = datetime(2026, 10, 3, 12, tzinfo=UTC)

    async with async_session_factory() as session:
        session.add(UserModel(id=passenger_id, phone=f"+225{passenger_id.int % 10_000_000_000:010d}", role="user"))
        session.add(_ride(ride_id, passenger_id, driver_id, Decimal("8000"), Decimal("2000"), settled_at))
        session.add(
            payment_orm.TransactionModel(
                id=uuid4(),
                ride_id=ride_id,
                amount=Decimal("10000"),
                method="cash",
                status="collected",
                collected_at=settled_at,
                created_at=settled_at,
            )
        )
        await session.commit()

    response = await client.get(
        "/v1/drivers/me/wallet/earnings",
        params={"period": "day", "from": "2026-10-03", "to": "2026-10-03"},
        headers=driver,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["timezone"] == "Africa/Abidjan"
    assert payload["summary"]["ride_earnings_xof"] == 8000
    assert payload["summary"]["platform_commissions_xof"] == 2000
    assert payload["summary"]["available_balance_xof"] >= 0
    await engine.dispose()


def _ride(ride_id, passenger_id, driver_id, payout, commission, completed_at):
    return ride_orm.RideModel(
        id=ride_id,
        passenger_user_id=passenger_id,
        driver_id=driver_id,
        status="completed",
        pickup_location=_point(),
        dropoff_location=_point(),
        requested_at=completed_at,
        completed_at=completed_at,
        driver_payout_estimate=payout,
        platform_commission=commission,
    )
