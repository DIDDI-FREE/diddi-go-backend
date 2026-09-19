"""Business definitions for Pilotage's daily DiddiGo totals."""

import re
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.ride.domain.interfaces import RideSummaryRepository

ABIDJAN_TIMEZONE = ZoneInfo("Africa/Abidjan")


class RideSummaryService:
    def __init__(self, repository: RideSummaryRepository) -> None:
        self._repository = repository

    async def daily_summary(self, day: str) -> dict:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) is None:
            raise ApiError(422, "INVALID_DATE", "La date doit suivre le format YYYY-MM-DD.")
        try:
            selected_day = date.fromisoformat(day)
            next_day = selected_day + timedelta(days=1)
        except ValueError as exc:
            raise ApiError(422, "INVALID_DATE", "Date calendaire invalide.") from exc
        except OverflowError as exc:
            raise ApiError(422, "INVALID_DATE", "Date hors plage acceptee.") from exc

        today = datetime.now(ABIDJAN_TIMEZONE).date()
        if selected_day > today:
            raise ApiError(422, "SUMMARY_DATE_IN_FUTURE", "La date ne peut pas etre dans le futur.")
        oldest_allowed = today - timedelta(days=settings.ride_summary_max_age_days)
        if selected_day < oldest_allowed:
            raise ApiError(
                422,
                "SUMMARY_DATE_OUT_OF_RANGE",
                f"La date doit etre comprise entre {oldest_allowed.isoformat()} et {today.isoformat()}.",
            )

        start = datetime.combine(selected_day, time.min, tzinfo=ABIDJAN_TIMEZONE).astimezone(UTC)
        end = datetime.combine(next_day, time.min, tzinfo=ABIDJAN_TIMEZONE).astimezone(UTC)
        totals = await self._repository.summarize_period(start, end)
        if totals.completed_rides_without_fare:
            log_event(
                "ride.summary.missing_final_fare",
                level="warning",
                date=day,
                count=totals.completed_rides_without_fare,
            )
        if totals.completed_fare_total_xof != totals.completed_fare_total_xof.to_integral_value():
            log_event("ride.summary.non_integral_xof", level="error", date=day)
            raise ApiError(500, "INVALID_RIDE_FARE", "Montant XOF non entier dans les courses terminees.")

        return {
            "module": "diddigo",
            "date": day,
            "timezone": "Africa/Abidjan",
            "rides_requested": totals.rides_requested,
            "rides_completed": totals.rides_completed,
            "completed_fare_total_xof": int(totals.completed_fare_total_xof),
            "calculated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
