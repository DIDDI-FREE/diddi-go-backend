from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.summary_service import ABIDJAN_TIMEZONE, RideSummaryService
from app_base.modules.ride.domain.summary import RideSummaryTotals


class FakeRideSummaryRepository:
    def __init__(self, totals: RideSummaryTotals) -> None:
        self.totals = totals
        self.period = None

    async def summarize_period(self, start, end):
        self.period = (start, end)
        return self.totals


def _service(totals: RideSummaryTotals | None = None) -> tuple[RideSummaryService, FakeRideSummaryRepository]:
    repository = FakeRideSummaryRepository(
        totals
        or RideSummaryTotals(
            rides_requested=12,
            rides_completed=8,
            completed_fare_total_xof=Decimal("24000"),
            completed_rides_without_fare=0,
        )
    )
    return RideSummaryService(repository), repository


@pytest.mark.unit
async def test_daily_summary_returns_pilotage_contract() -> None:
    service, repository = _service()
    today = datetime.now(ABIDJAN_TIMEZONE).date().isoformat()

    result = await service.daily_summary(today)

    assert result["date"] == today
    assert result["rides_requested"] == 12
    assert result["rides_completed"] == 8
    assert result["completed_fare_total_xof"] == 24000
    assert result["timezone"] == "Africa/Abidjan"
    assert repository.period[0].tzinfo == UTC
    assert repository.period[1] > repository.period[0]


@pytest.mark.unit
@pytest.mark.parametrize("value", ["19-09-2026", "2026-02-30", "not-a-date"])
async def test_daily_summary_rejects_invalid_date(value: str) -> None:
    service, _ = _service()

    with pytest.raises(ApiError) as error:
        await service.daily_summary(value)

    assert error.value.status_code == 422
    assert error.value.code == "INVALID_DATE"


@pytest.mark.unit
async def test_daily_summary_rejects_future_date() -> None:
    service, _ = _service()

    with pytest.raises(ApiError) as error:
        await service.daily_summary("2999-01-01")

    assert error.value.code == "SUMMARY_DATE_IN_FUTURE"


@pytest.mark.unit
async def test_daily_summary_rejects_date_outside_reporting_window() -> None:
    service, _ = _service()

    with pytest.raises(ApiError) as error:
        await service.daily_summary("2000-01-01")

    assert error.value.code == "SUMMARY_DATE_OUT_OF_RANGE"
