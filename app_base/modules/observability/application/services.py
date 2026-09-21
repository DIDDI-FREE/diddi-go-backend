from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app_base.core.errors import ApiError
from app_base.modules.observability.domain.interfaces import OperationalLogRepository

_ALLOWED_FIELDS = {"ride_id", "driver_id"}


class OperationalLogSearchService:
    def __init__(self, repository: OperationalLogRepository) -> None:
        self._repository = repository

    async def search(
        self,
        *,
        field: str,
        value: str,
        start: datetime | None,
        end: datetime | None,
        level: str | None,
        limit: int,
        cursor: str | None,
    ) -> dict:
        if field not in _ALLOWED_FIELDS:
            raise ValueError(f"Unsupported operational log field: {field}")

        effective_end = _as_utc(end or datetime.now(UTC))
        effective_start = _as_utc(start or (effective_end - timedelta(hours=24)))
        if effective_start >= effective_end:
            raise ApiError(422, "INVALID_LOG_TIME_RANGE", "La date de debut doit preceder la date de fin.")
        if effective_end - effective_start > timedelta(days=30):
            raise ApiError(
                422,
                "LOG_TIME_RANGE_TOO_LARGE",
                "La recherche de logs est limitee a 30 jours.",
            )

        normalized_level = level.upper() if level else None
        return await self._repository.search(
            field=field,
            value=value,
            start=effective_start,
            end=effective_end,
            level=normalized_level,
            limit=limit,
            cursor=cursor,
        )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
