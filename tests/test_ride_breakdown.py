"""Pilotage breakdown v1 domain, SQL, cache, and HTTP contract tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from redis.exceptions import RedisError
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError

from app_base.core.deps import ride_breakdown_service
from app_base.core.errors import ApiError, api_error_handler
from app_base.modules.ride.application.breakdown_service import ABIDJAN_TIMEZONE, RideBreakdownService
from app_base.modules.ride.domain.breakdown import (
    BreakdownDimension,
    BreakdownItem,
    BreakdownMetric,
    RideBreakdown,
)
from app_base.modules.ride.infra.breakdown_cache import RedisRideBreakdownCache
from app_base.modules.ride.infra.breakdown_repository import SqlAlchemyRideBreakdownRepository
from app_base.modules.ride.presentation.summary_router import require_pilotage, router

pytestmark = pytest.mark.unit


class FakeRepository:
    def __init__(self, items=()) -> None:
        self.items = tuple(items)
        self.calls = []

    async def aggregate(self, start, end, dimension, metric):
        self.calls.append((start, end, dimension, metric))
        return self.items


class FakeCache:
    def __init__(self, value=None, *, fail_read=False, fail_write=False) -> None:
        self.value = value
        self.fail_read = fail_read
        self.fail_write = fail_write
        self.writes = []

    async def get(self, day, dimension, metric):
        if self.fail_read:
            raise RedisError("down")
        return self.value

    async def set(self, day, dimension, metric, result, *, ttl_seconds):
        if self.fail_write:
            raise RedisError("down")
        self.writes.append((day, dimension, metric, result, ttl_seconds))


def recent_day(*, days_ago: int = 1) -> str:
    return (datetime.now(ABIDJAN_TIMEZONE).date() - timedelta(days=days_ago)).isoformat()


@pytest.mark.asyncio
async def test_payment_method_completed_contract_and_unknown_key() -> None:
    repository = FakeRepository(
        [
            BreakdownItem("cash", Decimal("6")),
            BreakdownItem("future_method", Decimal("4")),
        ]
    )
    result = await RideBreakdownService(repository, FakeCache()).breakdown(
        recent_day(), "payment_method", "rides_completed"
    )

    assert result["contract_version"] == "pilotage.breakdown.v1"
    assert result["timezone"] == "Africa/Abidjan"
    assert result["total"] == 10
    assert result["items"] == [
        {"key": "cash", "label": "Espèces", "value": 6},
        {"key": "future_method", "label": "future_method", "value": 4},
    ]
    assert sum(item["value"] for item in result["items"]) == result["total"]
    assert result["is_final"] is True


@pytest.mark.asyncio
async def test_xof_breakdown_preserves_decimal_precision() -> None:
    repository = FakeRepository([BreakdownItem("wave", Decimal("120.50"))])
    result = await RideBreakdownService(repository, FakeCache()).breakdown(
        recent_day(), "payment_method", "completed_fare_total_xof"
    )

    assert result["unit"] == "XOF"
    assert result["total"] == Decimal("120.50")
    assert result["items"][0]["value"] == Decimal("120.50")


@pytest.mark.asyncio
async def test_unsupported_combination_is_404_not_empty_success() -> None:
    repository = FakeRepository()
    with pytest.raises(ApiError) as error:
        await RideBreakdownService(repository, FakeCache()).breakdown(
            recent_day(), "final_status", "rides_completed"
        )

    assert error.value.status_code == 404
    assert error.value.code == "BREAKDOWN_NOT_AVAILABLE"
    assert repository.calls == []


@pytest.mark.asyncio
async def test_valid_empty_day_returns_real_empty_breakdown() -> None:
    result = await RideBreakdownService(FakeRepository(), FakeCache()).breakdown(
        recent_day(), "service_type", "rides_completed"
    )
    assert result["total"] == 0
    assert result["items"] == []


@pytest.mark.asyncio
async def test_cache_hit_skips_database() -> None:
    cached = RideBreakdown(
        total=Decimal("2"),
        items=(BreakdownItem("cash", Decimal("2")),),
        calculated_at=datetime(2026, 10, 2, tzinfo=UTC),
    )
    repository = FakeRepository()
    result = await RideBreakdownService(repository, FakeCache(cached)).breakdown(
        recent_day(), "payment_method", "rides_completed"
    )
    assert result["total"] == 2
    assert repository.calls == []


@pytest.mark.asyncio
async def test_cache_failure_falls_back_to_database_without_faking_data() -> None:
    repository = FakeRepository([BreakdownItem("standard", Decimal("3"))])
    result = await RideBreakdownService(repository, FakeCache(fail_read=True, fail_write=True)).breakdown(
        recent_day(), "service_type", "rides_completed"
    )
    assert result["total"] == 3
    assert len(repository.calls) == 1


@pytest.mark.asyncio
async def test_final_and_current_days_use_different_ttls() -> None:
    final_cache = FakeCache()
    current_cache = FakeCache()
    await RideBreakdownService(FakeRepository(), final_cache).breakdown(
        recent_day(), "hour", "rides_requested"
    )
    await RideBreakdownService(FakeRepository(), current_cache).breakdown(
        recent_day(days_ago=0), "hour", "rides_requested"
    )
    assert final_cache.writes[0][-1] > current_cache.writes[0][-1]


@pytest.mark.asyncio
async def test_inconsistent_cached_total_is_rejected() -> None:
    cached = RideBreakdown(
        total=Decimal("10"),
        items=(BreakdownItem("cash", Decimal("9")),),
        calculated_at=datetime.now(UTC),
    )
    with pytest.raises(ApiError) as error:
        await RideBreakdownService(FakeRepository(), FakeCache(cached)).breakdown(
            recent_day(), "payment_method", "rides_completed"
        )
    assert error.value.code == "BREAKDOWN_TOTAL_MISMATCH"


@pytest.mark.asyncio
async def test_database_failure_is_explicit() -> None:
    class FailingRepository:
        async def aggregate(self, *args):
            raise SQLAlchemyError("private database details")

    with pytest.raises(ApiError) as error:
        await RideBreakdownService(FailingRepository(), FakeCache()).breakdown(
            recent_day(), "hour", "rides_requested"
        )
    assert error.value.status_code == 503
    assert error.value.code == "RIDE_BREAKDOWN_UNAVAILABLE"


class FakeResult:
    def __init__(self, rows) -> None:
        self._rows = rows

    def all(self):
        return self._rows


class FakeSession:
    def __init__(self, rows) -> None:
        self.rows = rows
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return FakeResult(self.rows)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("dimension", "metric", "expected_sql", "expected_timestamp"),
    [
        (BreakdownDimension.HOUR, BreakdownMetric.RIDES_REQUESTED, "to_char", "requested_at"),
        (
            BreakdownDimension.PAYMENT_METHOD,
            BreakdownMetric.RIDES_REQUESTED,
            "payment_method",
            "requested_at",
        ),
        (
            BreakdownDimension.SERVICE_TYPE,
            BreakdownMetric.RIDES_REQUESTED,
            "vehicle_category",
            "requested_at",
        ),
        (BreakdownDimension.FINAL_STATUS, BreakdownMetric.RIDES_REQUESTED, "status", "requested_at"),
    ],
)
async def test_repository_uses_whitelisted_grouping(dimension, metric, expected_sql, expected_timestamp) -> None:
    session = FakeSession([SimpleNamespace(breakdown_key="cash", breakdown_value=2)])
    items = await SqlAlchemyRideBreakdownRepository(session).aggregate(
        datetime(2026, 10, 2, tzinfo=UTC),
        datetime(2026, 10, 3, tzinfo=UTC),
        dimension,
        metric,
    )
    sql = str(session.statements[0].compile(dialect=postgresql.dialect()))
    assert expected_sql in sql
    assert "GROUP BY" in sql
    assert expected_timestamp in sql
    assert items == (BreakdownItem("cash", Decimal("2")),)


@pytest.mark.asyncio
async def test_repository_completed_metric_filters_status_and_timestamp() -> None:
    session = FakeSession([SimpleNamespace(breakdown_key="wave", breakdown_value=Decimal("4500.50"))])
    await SqlAlchemyRideBreakdownRepository(session).aggregate(
        datetime(2026, 10, 2, tzinfo=UTC),
        datetime(2026, 10, 3, tzinfo=UTC),
        BreakdownDimension.PAYMENT_METHOD,
        BreakdownMetric.COMPLETED_FARE_TOTAL_XOF,
    )
    sql = str(session.statements[0].compile(dialect=postgresql.dialect()))
    assert "completed_at" in sql
    assert "status =" in sql
    assert "currency =" in sql
    assert "passenger_user_id" not in sql


class MemoryRedis:
    def __init__(self) -> None:
        self.values = {}
        self.ttl = None

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, *, ex):
        self.values[key] = value
        self.ttl = ex


@pytest.mark.asyncio
async def test_redis_cache_round_trips_decimal_without_loss() -> None:
    redis = MemoryRedis()
    cache = RedisRideBreakdownCache(redis)
    original = RideBreakdown(
        total=Decimal("4500.50"),
        items=(BreakdownItem("wave", Decimal("4500.50")),),
        calculated_at=datetime(2026, 10, 2, 12, tzinfo=UTC),
    )
    await cache.set("2026-10-02", "payment_method", "completed_fare_total_xof", original, ttl_seconds=300)
    restored = await cache.get("2026-10-02", "payment_method", "completed_fare_total_xof")
    assert restored == original
    assert redis.ttl == 300


class FakeBreakdownService:
    async def breakdown(self, day, dimension, metric):
        return {"date": day, "dimension": dimension, "metric": metric, "total": 0, "items": []}


def breakdown_app(*, authorized: bool) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.add_exception_handler(ApiError, api_error_handler)
    app.dependency_overrides[ride_breakdown_service] = lambda: FakeBreakdownService()
    if authorized:
        app.dependency_overrides[require_pilotage] = lambda: {"sub": "service:pilotage"}
    return app


@pytest.mark.asyncio
async def test_breakdown_route_requires_service_token() -> None:
    app = breakdown_app(authorized=False)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/internal/pilotage/breakdown?date=2026-10-02&dimension=hour&metric=rides_requested"
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_breakdown_route_returns_authorized_contract() -> None:
    app = breakdown_app(authorized=True)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/internal/pilotage/breakdown?date=2026-10-02&dimension=hour&metric=rides_requested"
        )
    assert response.status_code == 200
    assert response.json()["dimension"] == "hour"
