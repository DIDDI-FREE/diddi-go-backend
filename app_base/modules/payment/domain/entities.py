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
    created_at: datetime | None = None
    paid_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()
