"""Payment domain entities — plain dataclasses, no SQLAlchemy dependency."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class PaymentStatus(str, Enum):
    PENDING = "pending"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    COLLECTED = "collected"
    DISPUTED = "disputed"


class PaymentMethod(str, Enum):
    CASH = "cash"
    WAVE = "wave"
    DIDDIPAY = "diddipay"


@dataclass
class Transaction:
    id: UUID
    ride_id: UUID
    amount: Decimal
    currency: str = "XOF"
    method: PaymentMethod = PaymentMethod.CASH
    status: PaymentStatus = PaymentStatus.PENDING
    collected_by: UUID | None = None  # driver_profile.id
    collected_at: datetime | None = None
    created_at: datetime | None = None
    payment_intent_id: UUID | None = None
    business_reference: str | None = None
    idempotency_key: str | None = None
    provider_status: str | None = None
    paid_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()
