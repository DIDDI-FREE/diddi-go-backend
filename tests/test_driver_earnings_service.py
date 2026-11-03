from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.payment.application.wallet_service import DriverWalletService
from app_base.modules.payment.domain.entities import DriverEarningsBucket, DriverWallet

pytestmark = pytest.mark.unit


class FakeDriverRepo:
    def __init__(self, driver_id):
        self.driver_id = driver_id

    async def find_by_user_id(self, _user_id):
        return SimpleNamespace(id=self.driver_id)


class FakePaymentRepo:
    def __init__(self, buckets):
        self.buckets = buckets
        self.summary_request = None

    async def summarize_driver_earnings(self, driver_id, *, period, start, end):
        self.summary_request = (driver_id, period, start, end)
        return self.buckets

    async def get_or_create_wallet(self, driver_id):
        return DriverWallet(id=uuid4(), driver_id=driver_id, balance=Decimal("4200"))


@pytest.mark.asyncio
async def test_driver_earnings_sums_confirmed_business_buckets_in_abidjan_period() -> None:
    driver_id = uuid4()
    user_id = uuid4()
    repo = FakePaymentRepo(
        [
            DriverEarningsBucket(
                period_start=date(2026, 10, 1),
                ride_earnings=Decimal("8000"),
                platform_commissions=Decimal("2000"),
                withdrawals_succeeded=Decimal("3000"),
                pending_or_disputed=Decimal("500"),
            ),
            DriverEarningsBucket(
                period_start=date(2026, 10, 2),
                ride_earnings=Decimal("4000"),
                platform_commissions=Decimal("1000"),
            ),
        ]
    )
    service = DriverWalletService(payment_repo=repo, driver_repo=FakeDriverRepo(driver_id))

    result = await service.get_earnings(
        driver_user_id=user_id,
        period="day",
        from_date=date(2026, 10, 1),
        to_date=date(2026, 10, 2),
    )

    assert repo.summary_request == (
        driver_id,
        "day",
        datetime(2026, 10, 1, tzinfo=UTC),
        datetime(2026, 10, 3, tzinfo=UTC),
    )
    assert result["timezone"] == "Africa/Abidjan"
    assert result["summary"] == {
        "ride_earnings_xof": 12000,
        "platform_commissions_xof": 3000,
        "withdrawals_succeeded_xof": 3000,
        "pending_or_disputed_xof": 500,
        "available_balance_xof": 4200,
    }


@pytest.mark.asyncio
async def test_driver_earnings_rejects_invalid_or_unbounded_periods() -> None:
    service = DriverWalletService(payment_repo=FakePaymentRepo([]), driver_repo=FakeDriverRepo(uuid4()))
    user_id = uuid4()

    with pytest.raises(ApiError) as invalid_period:
        await service.get_earnings(
            driver_user_id=user_id,
            period="quarter",
            from_date=date(2026, 10, 1),
            to_date=date(2026, 10, 2),
        )
    assert invalid_period.value.code == "INVALID_EARNINGS_PERIOD"

    with pytest.raises(ApiError) as oversized_period:
        await service.get_earnings(
            driver_user_id=user_id,
            period="month",
            from_date=date(2025, 1, 1),
            to_date=date(2026, 1, 3),
        )
    assert oversized_period.value.code == "INVALID_EARNINGS_PERIOD"
