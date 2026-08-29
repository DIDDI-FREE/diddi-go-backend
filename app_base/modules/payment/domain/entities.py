"""Payment domain entities — plain dataclasses, no SQLAlchemy dependency."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class _Keep:
    """Sentinel for repository writes: leave the stored value untouched.

    `None` is a meaningful value for `provider_next_action` (it clears the
    checkout URL), so "not supplied" needs to be distinguishable from it.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover — debugging aid
        return "KEEP"


KEEP = _Keep()


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


class WalletEntryDirection(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class WalletEntryStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class WalletEntryType(str, Enum):
    RIDE_PAYOUT = "ride_payout"
    PLATFORM_COMMISSION = "platform_commission"
    TOPUP = "topup"
    ADJUSTMENT = "adjustment"


class TopupStatus(str, Enum):
    PENDING = "pending"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Statuses where DiddiPay still owns the outcome: a callback is expected, so a
# row stuck here past its grace period is exactly what reconciliation re-reads.
PENDING_PAYMENT_STATUSES = frozenset(
    {PaymentStatus.PENDING, PaymentStatus.REQUIRES_ACTION, PaymentStatus.PROCESSING},
)
PENDING_TOPUP_STATUSES = frozenset(
    {TopupStatus.PENDING, TopupStatus.REQUIRES_ACTION, TopupStatus.PROCESSING},
)


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
    provider_next_action: dict[str, Any] | None = None
    paid_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class DriverWallet:
    id: UUID
    driver_id: UUID
    balance: Decimal = Decimal("0")
    currency: str = "XOF"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class DriverLedgerEntry:
    id: UUID
    driver_id: UUID
    amount: Decimal
    currency: str
    direction: WalletEntryDirection
    entry_type: WalletEntryType
    status: WalletEntryStatus
    reference_type: str
    reference_id: UUID
    description: str | None = None
    created_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class DriverTopup:
    id: UUID
    driver_id: UUID
    amount: Decimal
    currency: str = "XOF"
    method: PaymentMethod = PaymentMethod.DIDDIPAY
    status: TopupStatus = TopupStatus.PENDING
    payment_intent_id: UUID | None = None
    business_reference: str | None = None
    idempotency_key: str | None = None
    provider_status: str | None = None
    provider_next_action: dict[str, Any] | None = None
    created_at: datetime | None = None
    paid_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()
