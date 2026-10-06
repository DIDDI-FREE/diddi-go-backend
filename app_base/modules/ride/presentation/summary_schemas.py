"""Typed OpenAPI contracts for internal Pilotage summaries."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

FinanceMetricName = Literal[
    "completed_fare_total_xof",
    "digital_payments_xof",
    "cash_payments_xof",
    "platform_commission_xof",
    "driver_earnings_xof",
    "driver_amount_paid_xof",
    "driver_amount_outstanding_xof",
    "refunds_xof",
    "driver_topups_requested_count",
    "driver_topups_requested_xof",
    "driver_topups_succeeded_count",
    "driver_topups_succeeded_xof",
    "driver_topups_pending_count",
    "driver_topups_pending_xof",
    "driver_topups_failed_count",
    "driver_topups_failed_xof",
]


class PilotageMetric(BaseModel):
    name: FinanceMetricName
    value: int
    unit: Literal["XOF", "count"]


class PilotageSource(BaseModel):
    module: str
    record_type: str


class PilotageFinanceSummaryResponse(BaseModel):
    contract_version: Literal["pilotage.v1"]
    module: Literal["diddigo"]
    date: date
    timezone: Literal["Africa/Abidjan"]
    is_final: bool
    metrics: list[PilotageMetric]
    calculated_at: datetime
    sources: list[PilotageSource]
