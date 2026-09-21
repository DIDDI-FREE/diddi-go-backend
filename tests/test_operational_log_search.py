from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app_base.core.errors import ApiError
from app_base.modules.observability.application.services import OperationalLogSearchService
from app_base.modules.observability.infra.loki import _build_query, _parse_loki_result

pytestmark = pytest.mark.unit


class FakeLogRepository:
    def __init__(self) -> None:
        self.call = None

    async def search(self, **kwargs) -> dict:
        self.call = kwargs
        return {"items": [], "next_cursor": None}


@pytest.mark.asyncio
async def test_search_defaults_to_last_24_hours_and_normalizes_level() -> None:
    repository = FakeLogRepository()
    service = OperationalLogSearchService(repository)
    end = datetime(2026, 9, 21, 12, tzinfo=UTC)

    result = await service.search(
        field="ride_id",
        value="ride-1",
        start=None,
        end=end,
        level="warning",
        limit=25,
        cursor=None,
    )

    assert result["items"] == []
    assert repository.call["start"] == end - timedelta(hours=24)
    assert repository.call["end"] == end
    assert repository.call["level"] == "WARNING"
    assert repository.call["limit"] == 25


@pytest.mark.asyncio
async def test_search_rejects_ranges_over_30_days() -> None:
    service = OperationalLogSearchService(FakeLogRepository())
    end = datetime(2026, 9, 21, tzinfo=UTC)

    with pytest.raises(ApiError) as raised:
        await service.search(
            field="driver_id",
            value="driver-1",
            start=end - timedelta(days=31),
            end=end,
            level=None,
            limit=100,
            cursor=None,
        )

    assert raised.value.code == "LOG_TIME_RANGE_TOO_LARGE"


def test_loki_query_uses_exact_json_field_filters() -> None:
    query = _build_query("app", "ride_id", "ride-1", "ERROR")

    assert query == '{compose_service="app"} | json | ride_id="ride-1" | level="ERROR"'


def test_loki_result_is_normalized_and_sorted_newest_first() -> None:
    payload = {
        "status": "success",
        "data": {
            "result": [
                {
                    "stream": {"compose_service": "app"},
                    "values": [
                        ["1000000000", '{"event":"ride.created","level":"INFO","ride_id":"r1"}'],
                        ["2000000000", '{"event":"ride.accepted","level":"INFO","ride_id":"r1"}'],
                    ],
                }
            ]
        },
    }

    entries = _parse_loki_result(payload)

    assert [entry["event"] for entry in entries] == ["ride.accepted", "ride.created"]
    assert entries[0]["metadata"] == {"ride_id": "r1"}
