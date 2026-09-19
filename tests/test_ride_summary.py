"""Pilotage daily summary contract and access checks."""

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

from app_base.core.deps import ride_summary_service
from app_base.core.errors import ApiError, api_error_handler
from app_base.modules.ride.application.summary_service import RideSummaryService
from app_base.modules.ride.domain.summary import RideSummaryTotals
from app_base.modules.ride.infra.summary_repository import SqlAlchemyRideSummaryRepository
from app_base.modules.ride.presentation.summary_router import require_pilotage, router

pytestmark = pytest.mark.unit


class FakeSummaryRepository:
    def __init__(self, totals: RideSummaryTotals) -> None:
        self.totals = totals
        self.period = None

    async def summarize_period(self, start, end) -> RideSummaryTotals:
        self.period = (start, end)
        return self.totals


def totals(
    requested: int = 0,
    completed: int = 0,
    fare: str = "0",
    missing_fare: int = 0,
) -> RideSummaryTotals:
    return RideSummaryTotals(requested, completed, Decimal(fare), missing_fare)


@pytest.mark.asyncio
async def test_daily_summary_uses_abidjan_day_and_exact_totals() -> None:
    repository = FakeSummaryRepository(totals(3, 2, "4500"))

    result = await RideSummaryService(repository).daily_summary("2026-09-19")

    assert repository.period == (
        datetime(2026, 9, 19, tzinfo=UTC),
        datetime(2026, 9, 20, tzinfo=UTC),
    )
    assert result["module"] == "diddigo"
    assert result["date"] == "2026-09-19"
    assert result["timezone"] == "Africa/Abidjan"
    assert result["rides_requested"] == 3
    assert result["rides_completed"] == 2
    assert result["completed_fare_total_xof"] == 4500
    assert result["calculated_at"].endswith("Z")


@pytest.mark.asyncio
async def test_empty_day_returns_zeros() -> None:
    result = await RideSummaryService(FakeSummaryRepository(totals())).daily_summary("2026-09-19")

    assert (result["rides_requested"], result["rides_completed"], result["completed_fare_total_xof"]) == (0, 0, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize("day", ["2026-02-30", "19-09-2026", "2026-09-19T00:00:00", "9999-12-31"])
async def test_invalid_calendar_day_is_rejected(day: str) -> None:
    repository = FakeSummaryRepository(totals())

    with pytest.raises(ApiError) as error:
        await RideSummaryService(repository).daily_summary(day)

    assert error.value.status_code == 422
    assert error.value.code == "INVALID_DATE"
    assert repository.period is None


@pytest.mark.asyncio
async def test_missing_final_fare_is_counted_but_not_added(monkeypatch) -> None:
    events = []
    monkeypatch.setattr(
        "app_base.modules.ride.application.summary_service.log_event",
        lambda *args, **kwargs: events.append((args, kwargs)),
    )

    result = await RideSummaryService(FakeSummaryRepository(totals(1, 1, "0", 1))).daily_summary("2026-09-19")

    assert result["rides_completed"] == 1
    assert result["completed_fare_total_xof"] == 0
    assert events[0][0] == ("ride.summary.missing_final_fare",)
    assert events[0][1]["count"] == 1


@pytest.mark.asyncio
async def test_fractional_xof_is_not_silently_truncated(monkeypatch) -> None:
    monkeypatch.setattr("app_base.modules.ride.application.summary_service.log_event", lambda *args, **kwargs: None)

    with pytest.raises(ApiError) as error:
        await RideSummaryService(FakeSummaryRepository(totals(1, 1, "120.50"))).daily_summary("2026-09-19")

    assert error.value.code == "INVALID_RIDE_FARE"


class FakeSession:
    def __init__(self) -> None:
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return SimpleNamespace(
            one=lambda: SimpleNamespace(
                rides_requested=3,
                rides_completed=2,
                completed_fare_total_xof=Decimal("4500"),
                completed_rides_without_fare=1,
            )
        )


@pytest.mark.asyncio
async def test_repository_aggregates_in_one_sql_statement() -> None:
    session = FakeSession()
    result = await SqlAlchemyRideSummaryRepository(session).summarize_period(
        datetime(2026, 9, 19, tzinfo=UTC),
        datetime(2026, 9, 20, tzinfo=UTC),
    )

    sql = str(session.statements[0].compile(dialect=postgresql.dialect()))
    assert len(session.statements) == 1
    assert "requested_at >=" in sql and "requested_at <" in sql
    assert "completed_at >=" in sql and "completed_at <" in sql
    assert "status =" in sql and "currency =" in sql
    assert result == totals(3, 2, "4500", 1)


def summary_app(repository: FakeSummaryRepository, *, authorized: bool = False) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.add_exception_handler(ApiError, api_error_handler)
    app.dependency_overrides[ride_summary_service] = lambda: RideSummaryService(repository)
    if authorized:
        app.dependency_overrides[require_pilotage] = lambda: {"sub": "service:pilotage"}
    return app


@pytest.mark.asyncio
async def test_summary_route_rejects_missing_service_token() -> None:
    repository = FakeSummaryRepository(totals())
    app = summary_app(repository)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/internal/v1/ride-summary?date=2026-09-19")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_MISSING"
    assert repository.period is None


@pytest.mark.asyncio
async def test_summary_route_rejects_missing_client_id() -> None:
    repository = FakeSummaryRepository(totals())
    app = summary_app(repository)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/internal/v1/ride-summary?date=2026-09-19",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SERVICE_CLIENT_ID_MISSING"
    assert repository.period is None


@pytest.mark.asyncio
async def test_summary_route_rejects_missing_scope(monkeypatch) -> None:
    def deny_scope(*args, **kwargs):
        raise ApiError(403, "SERVICE_SCOPE_INVALID", "Scope insuffisant.")

    monkeypatch.setattr("app_base.core.auth_deps.decode_identity_service_token", deny_scope)
    repository = FakeSummaryRepository(totals())
    app = summary_app(repository)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/internal/v1/ride-summary?date=2026-09-19",
            headers={"Authorization": "Bearer fake-token", "X-Client-ID": "pilotage-staging-diddigo"},
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SERVICE_SCOPE_INVALID"
    assert repository.period is None


@pytest.mark.asyncio
async def test_summary_route_returns_report_to_authorized_pilotage() -> None:
    repository = FakeSummaryRepository(totals(3, 2, "4500"))
    app = summary_app(repository, authorized=True)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/internal/v1/ride-summary?date=2026-09-19")

    assert response.status_code == 200
    assert response.json()["completed_fare_total_xof"] == 4500


@pytest.mark.asyncio
async def test_summary_route_reports_sql_failure_without_leaking_details(monkeypatch) -> None:
    class FailingRepository:
        async def summarize_period(self, start, end):
            raise SQLAlchemyError("private database connection details")

    events = []
    monkeypatch.setattr(
        "app_base.modules.ride.application.summary_service.log_event",
        lambda *args, **kwargs: events.append((args, kwargs)),
    )
    app = summary_app(FailingRepository(), authorized=True)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/internal/v1/ride-summary?date=2026-09-19")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "RIDE_SUMMARY_UNAVAILABLE"
    assert "private database" not in response.text
    assert events[0][0] == ("ride.summary.database_error",)
