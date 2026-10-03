"""Application service for the Pilotage breakdown v1 contract."""

import re
import time as monotonic_time
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.metrics import increment
from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.ride.domain.breakdown import (
    SUPPORTED_BREAKDOWNS,
    BreakdownDimension,
    BreakdownMetric,
    RideBreakdown,
)
from app_base.modules.ride.domain.interfaces import RideBreakdownCache, RideBreakdownRepository

ABIDJAN_TIMEZONE = ZoneInfo("Africa/Abidjan")
LABELS = {
    "cash": "Espèces",
    "wave": "Wave",
    "diddipay": "DiddiPay",
    "standard": "Standard",
    "comfort": "Confort",
    "van": "Van",
}


class RideBreakdownService:
    def __init__(self, repository: RideBreakdownRepository, cache: RideBreakdownCache) -> None:
        self._repository = repository
        self._cache = cache

    async def breakdown(self, day: str, raw_dimension: str, raw_metric: str) -> dict:
        started = monotonic_time.perf_counter()
        log_event("pilotage.breakdown.requested", date=day, dimension=raw_dimension, metric=raw_metric)
        try:
            selected_day, start, end = self._period(day)
            dimension, metric = self._selection(raw_dimension, raw_metric)
            cached = await self._cache_get(day, dimension, metric)
            cache_status = "hit" if cached is not None else "miss"
            result = cached or await self._calculate(start, end, dimension, metric)
            if cached is None:
                await self._cache_set(day, selected_day, dimension, metric, result)
            if not result.is_consistent():
                log_event(
                    "pilotage.breakdown.integrity_error",
                    level="error",
                    date=day,
                    dimension=dimension.value,
                    metric=metric.value,
                )
                raise ApiError(500, ErrorCode.BREAKDOWN_TOTAL_MISMATCH, "Ventilation Pilotage incoherente.")
            response = self._response(day, selected_day, dimension, metric, result)
            duration_ms = round((monotonic_time.perf_counter() - started) * 1000, 2)
            log_event(
                "pilotage.breakdown.succeeded",
                date=day,
                dimension=dimension.value,
                metric=metric.value,
                items_count=len(result.items),
                cache_status=cache_status,
                duration_ms=duration_ms,
            )
            self._record_metrics(dimension, metric, "success", cache_status, duration_ms)
            return response
        except ApiError as exc:
            duration_ms = round((monotonic_time.perf_counter() - started) * 1000, 2)
            log_event(
                "pilotage.breakdown.rejected",
                level="warning",
                date=day,
                dimension=raw_dimension,
                metric=raw_metric,
                error_code=exc.code,
            )
            safe_dimension = raw_dimension if raw_dimension in BreakdownDimension._value2member_map_ else "unknown"
            safe_metric = raw_metric if raw_metric in BreakdownMetric._value2member_map_ else "unknown"
            labels = {
                "dimension": safe_dimension,
                "metric": safe_metric,
                "status": "rejected",
                "cache_status": "not_used",
            }
            increment("diddigo_pilotage_breakdown_requests_total", labels)
            increment("diddigo_pilotage_breakdown_duration_ms_count", labels)
            increment("diddigo_pilotage_breakdown_duration_ms_sum", labels, duration_ms)
            raise

    @staticmethod
    def _period(day: str) -> tuple[date, datetime, datetime]:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) is None:
            raise ApiError(422, "INVALID_DATE", "La date doit suivre le format YYYY-MM-DD.")
        try:
            selected_day = date.fromisoformat(day)
            next_day = selected_day + timedelta(days=1)
        except (ValueError, OverflowError) as exc:
            raise ApiError(422, "INVALID_DATE", "Date calendaire invalide.") from exc
        today = datetime.now(ABIDJAN_TIMEZONE).date()
        if selected_day > today:
            raise ApiError(422, "SUMMARY_DATE_IN_FUTURE", "La date ne peut pas etre dans le futur.")
        oldest = today - timedelta(days=settings.ride_summary_max_age_days)
        if selected_day < oldest:
            raise ApiError(422, "SUMMARY_DATE_OUT_OF_RANGE", "Date hors plage Pilotage acceptee.")
        start = datetime.combine(selected_day, time.min, tzinfo=ABIDJAN_TIMEZONE).astimezone(UTC)
        end = datetime.combine(next_day, time.min, tzinfo=ABIDJAN_TIMEZONE).astimezone(UTC)
        return selected_day, start, end

    @staticmethod
    def _selection(raw_dimension: str, raw_metric: str) -> tuple[BreakdownDimension, BreakdownMetric]:
        try:
            dimension = BreakdownDimension(raw_dimension)
            metric = BreakdownMetric(raw_metric)
        except ValueError as exc:
            raise ApiError(404, ErrorCode.BREAKDOWN_NOT_AVAILABLE, "Ventilation Pilotage indisponible.") from exc
        if (dimension, metric) not in SUPPORTED_BREAKDOWNS:
            raise ApiError(404, ErrorCode.BREAKDOWN_NOT_AVAILABLE, "Ventilation Pilotage indisponible.")
        return dimension, metric

    async def _calculate(self, start, end, dimension, metric) -> RideBreakdown:
        try:
            items = await self._repository.aggregate(start, end, dimension, metric)
        except SQLAlchemyError as exc:
            log_event(
                "pilotage.breakdown.database_error",
                level="error",
                dimension=dimension.value,
                metric=metric.value,
            )
            raise ApiError(
                503,
                ErrorCode.RIDE_BREAKDOWN_UNAVAILABLE,
                "Ventilation temporairement indisponible.",
            ) from exc
        return RideBreakdown(
            total=sum((item.value for item in items), Decimal("0")),
            items=items,
            calculated_at=datetime.now(UTC),
        )

    async def _cache_get(self, day, dimension, metric):
        try:
            cached = await self._cache.get(day, dimension.value, metric.value)
            log_event(
                "pilotage.breakdown.cache_hit" if cached else "pilotage.breakdown.cache_miss",
                date=day,
                dimension=dimension.value,
                metric=metric.value,
            )
            return cached
        except (RedisError, ValueError, TypeError, KeyError) as exc:
            log_event(
                "pilotage.breakdown.cache_error",
                level="warning",
                operation="read",
                error_type=type(exc).__name__,
            )
            return None

    async def _cache_set(self, day, selected_day, dimension, metric, result) -> None:
        today = datetime.now(ABIDJAN_TIMEZONE).date()
        ttl = (
            settings.pilotage_breakdown_current_ttl_seconds
            if selected_day == today
            else settings.pilotage_breakdown_final_ttl_seconds
        )
        try:
            await self._cache.set(day, dimension.value, metric.value, result, ttl_seconds=ttl)
        except RedisError as exc:
            log_event(
                "pilotage.breakdown.cache_error",
                level="warning",
                operation="write",
                error_type=type(exc).__name__,
            )

    @staticmethod
    def _response(day, selected_day, dimension, metric, result) -> dict:
        is_count = metric is not BreakdownMetric.COMPLETED_FARE_TOTAL_XOF
        value = (lambda amount: int(amount)) if is_count else (lambda amount: amount)
        return {
            "contract_version": "pilotage.breakdown.v1",
            "module": "diddigo",
            "date": day,
            "timezone": "Africa/Abidjan",
            "dimension": dimension.value,
            "metric": metric.value,
            "unit": "count" if is_count else "XOF",
            "total": value(result.total),
            "items": [
                {"key": item.key, "label": LABELS.get(item.key, item.key), "value": value(item.value)}
                for item in result.items
            ],
            "is_final": selected_day < datetime.now(ABIDJAN_TIMEZONE).date(),
            "calculated_at": result.calculated_at.isoformat().replace("+00:00", "Z"),
        }

    @staticmethod
    def _record_metrics(dimension, metric, status, cache_status, duration_ms) -> None:
        labels = {
            "dimension": dimension.value,
            "metric": metric.value,
            "status": status,
            "cache_status": cache_status,
        }
        increment("diddigo_pilotage_breakdown_requests_total", labels)
        increment("diddigo_pilotage_breakdown_duration_ms_count", labels)
        increment("diddigo_pilotage_breakdown_duration_ms_sum", labels, duration_ms)
        increment(
            "diddigo_pilotage_breakdown_cache_total",
            {"dimension": dimension.value, "metric": metric.value, "cache_status": cache_status},
        )
