"""Business definitions for Pilotage's daily DiddiGo totals."""

import re
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.exc import SQLAlchemyError

from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.ride.domain.interfaces import RideSummaryRepository

ABIDJAN_TIMEZONE = ZoneInfo("Africa/Abidjan")


class RideSummaryService:
    def __init__(self, repository: RideSummaryRepository) -> None:
        self._repository = repository

    async def daily_summary(self, day: str) -> dict:
        selected_day, start, end = self._period_for_day(day)
        del selected_day
        try:
            totals = await self._repository.summarize_period(start, end)
        except SQLAlchemyError as exc:
            log_event("ride.summary.database_error", level="error", date=day)
            raise ApiError(503, "RIDE_SUMMARY_UNAVAILABLE", "Resume des courses temporairement indisponible.") from exc
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

    def _period_for_day(self, day: str) -> tuple[date, datetime, datetime]:
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
        return selected_day, start, end

    async def pilotage_daily_summary(self, day: str) -> dict:
        """Return the normalized DiddiFree Pilotage v1 projection."""
        summary = await self.daily_summary(day)
        selected_day = date.fromisoformat(summary["date"])
        today = datetime.now(ABIDJAN_TIMEZONE).date()
        return {
            "contract_version": "pilotage.v1",
            "module": summary["module"],
            "date": summary["date"],
            "timezone": summary["timezone"],
            "is_final": selected_day < today,
            "metrics": [
                {
                    "name": "rides_requested",
                    "label": "Courses demandees",
                    "value": summary["rides_requested"],
                    "unit": "count",
                },
                {
                    "name": "rides_completed",
                    "label": "Courses terminees",
                    "value": summary["rides_completed"],
                    "unit": "count",
                },
                {
                    "name": "completed_fare_total_xof",
                    "label": "Montant facture des courses terminees",
                    "value": summary["completed_fare_total_xof"],
                    "unit": "XOF",
                },
            ],
            "calculated_at": summary["calculated_at"],
            "sources": [{"module": "diddigo", "record_type": "ride-summary"}],
            "deep_links": [
                {
                    "label": "Ouvrir les courses dans Backoffice",
                    "href": "/backoffice/#diddigo-rides",
                },
            ],
        }

    async def pilotage_finance_summary(self, day: str) -> dict:
        selected_day, start, end = self._period_for_day(day)
        try:
            totals = await self._repository.summarize_finance_period(start, end)
        except SQLAlchemyError as exc:
            log_event("ride.finance_summary.database_error", level="error", date=day)
            raise ApiError(
                503,
                "RIDE_FINANCE_SUMMARY_UNAVAILABLE",
                "Resume financier temporairement indisponible.",
            ) from exc

        amounts = {
            name: value
            for name, value in vars(totals).items()
            if name.endswith("_xof")
        }
        if any(value != value.to_integral_value() for value in amounts.values()):
            raise ApiError(500, "INVALID_FINANCE_AMOUNT", "Montant XOF non entier dans le resume financier.")
        if totals.digital_payments_xof + totals.cash_payments_xof != totals.completed_fare_total_xof:
            raise ApiError(500, "PAYMENT_ALLOCATION_MISMATCH", "Ventilation des paiements incoherente.")
        if totals.platform_commission_xof + totals.driver_earnings_xof != totals.completed_fare_total_xof:
            raise ApiError(500, "FARE_ALLOCATION_MISMATCH", "Repartition du montant metier incoherente.")
        if totals.driver_amount_paid_xof > totals.driver_earnings_xof:
            raise ApiError(500, "DRIVER_PAYMENT_MISMATCH", "Montant chauffeur paye superieur aux gains.")

        outstanding = totals.driver_earnings_xof - totals.driver_amount_paid_xof
        metrics = [
            ("completed_fare_total_xof", totals.completed_fare_total_xof, "XOF"),
            ("digital_payments_xof", totals.digital_payments_xof, "XOF"),
            ("cash_payments_xof", totals.cash_payments_xof, "XOF"),
            ("platform_commission_xof", totals.platform_commission_xof, "XOF"),
            ("driver_earnings_xof", totals.driver_earnings_xof, "XOF"),
            ("driver_amount_paid_xof", totals.driver_amount_paid_xof, "XOF"),
            ("driver_amount_outstanding_xof", outstanding, "XOF"),
            ("refunds_xof", totals.refunds_xof, "XOF"),
            ("driver_topups_requested_count", totals.driver_topups_requested_count, "count"),
            ("driver_topups_requested_xof", totals.driver_topups_requested_xof, "XOF"),
            ("driver_topups_succeeded_count", totals.driver_topups_succeeded_count, "count"),
            ("driver_topups_succeeded_xof", totals.driver_topups_succeeded_xof, "XOF"),
            ("driver_topups_pending_count", totals.driver_topups_pending_count, "count"),
            ("driver_topups_pending_xof", totals.driver_topups_pending_xof, "XOF"),
            ("driver_topups_failed_count", totals.driver_topups_failed_count, "count"),
            ("driver_topups_failed_xof", totals.driver_topups_failed_xof, "XOF"),
        ]
        return {
            "contract_version": "pilotage.v1",
            "module": "diddigo",
            "date": day,
            "timezone": "Africa/Abidjan",
            "is_final": selected_day < datetime.now(ABIDJAN_TIMEZONE).date(),
            "metrics": [{"name": name, "value": int(value), "unit": unit} for name, value, unit in metrics],
            "calculated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "sources": [{"module": "diddigo", "record_type": "ride-finance-summary"}],
        }
