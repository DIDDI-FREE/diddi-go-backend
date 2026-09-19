"""Daily ride totals returned by the reporting repository."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RideSummaryTotals:
    rides_requested: int
    rides_completed: int
    completed_fare_total_xof: Decimal
    completed_rides_without_fare: int
