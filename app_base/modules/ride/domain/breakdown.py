"""Pilotage breakdown value objects and supported contract matrix."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class BreakdownDimension(str, Enum):
    HOUR = "hour"
    PAYMENT_METHOD = "payment_method"
    SERVICE_TYPE = "service_type"
    FINAL_STATUS = "final_status"


class BreakdownMetric(str, Enum):
    RIDES_REQUESTED = "rides_requested"
    RIDES_COMPLETED = "rides_completed"
    COMPLETED_FARE_TOTAL_XOF = "completed_fare_total_xof"


SUPPORTED_BREAKDOWNS = frozenset(
    {
        (BreakdownDimension.HOUR, BreakdownMetric.RIDES_REQUESTED),
        (BreakdownDimension.HOUR, BreakdownMetric.RIDES_COMPLETED),
        (BreakdownDimension.HOUR, BreakdownMetric.COMPLETED_FARE_TOTAL_XOF),
        (BreakdownDimension.PAYMENT_METHOD, BreakdownMetric.RIDES_REQUESTED),
        (BreakdownDimension.PAYMENT_METHOD, BreakdownMetric.RIDES_COMPLETED),
        (BreakdownDimension.PAYMENT_METHOD, BreakdownMetric.COMPLETED_FARE_TOTAL_XOF),
        (BreakdownDimension.SERVICE_TYPE, BreakdownMetric.RIDES_REQUESTED),
        (BreakdownDimension.SERVICE_TYPE, BreakdownMetric.RIDES_COMPLETED),
        (BreakdownDimension.SERVICE_TYPE, BreakdownMetric.COMPLETED_FARE_TOTAL_XOF),
        (BreakdownDimension.FINAL_STATUS, BreakdownMetric.RIDES_REQUESTED),
    }
)


@dataclass(frozen=True)
class BreakdownItem:
    key: str
    value: Decimal


@dataclass(frozen=True)
class RideBreakdown:
    total: Decimal
    items: tuple[BreakdownItem, ...]
    calculated_at: datetime

    def is_consistent(self) -> bool:
        return sum((item.value for item in self.items), Decimal("0")) == self.total
