"""Daily ride totals returned by the reporting repository."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RideSummaryTotals:
    rides_requested: int
    rides_completed: int
    completed_fare_total_xof: Decimal
    completed_rides_without_fare: int


@dataclass(frozen=True)
class RideFinanceSummaryTotals:
    completed_fare_total_xof: Decimal
    digital_payments_xof: Decimal
    cash_payments_xof: Decimal
    platform_commission_xof: Decimal
    driver_earnings_xof: Decimal
    driver_amount_paid_xof: Decimal
    refunds_xof: Decimal
    driver_topups_requested_count: int
    driver_topups_requested_xof: Decimal
    driver_topups_succeeded_count: int
    driver_topups_succeeded_xof: Decimal
    driver_topups_pending_count: int
    driver_topups_pending_xof: Decimal
    driver_topups_failed_count: int
    driver_topups_failed_xof: Decimal
    driver_withdrawals_requested_count: int = 0
    driver_withdrawals_requested_xof: Decimal = Decimal("0")
    driver_withdrawals_processing_count: int = 0
    driver_withdrawals_processing_xof: Decimal = Decimal("0")
    driver_withdrawals_succeeded_count: int = 0
    driver_withdrawals_succeeded_xof: Decimal = Decimal("0")
    driver_withdrawals_released_count: int = 0
    driver_withdrawals_released_xof: Decimal = Decimal("0")
    withdrawal_fees_xof: Decimal = Decimal("0")
