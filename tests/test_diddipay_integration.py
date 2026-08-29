from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.payment.application.services import PaymentService
from app_base.modules.payment.application.wallet_service import DriverWalletService
from app_base.modules.payment.domain.entities import (
    KEEP,
    PENDING_PAYMENT_STATUSES,
    PENDING_TOPUP_STATUSES,
    PaymentStatus,
    WalletEntryDirection,
    WalletEntryType,
)
from app_base.modules.ride.domain.entities import PaymentMethod as RidePaymentMethod
from app_base.modules.ride.domain.entities import Ride, RideStatus
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


class FakePaymentRepo:
    def __init__(self) -> None:
        self.payment = None
        self.events: set[str] = set()
        self.ledger = []
        self.wallets = {}
        self.topups = {}

    async def save(self, transaction):
        self.payment = transaction
        return transaction

    async def find_by_ride_id(self, ride_id):
        if self.payment and self.payment.ride_id == ride_id:
            return self.payment
        return None

    async def find_by_payment_intent_id(self, payment_intent_id):
        if self.payment and self.payment.payment_intent_id == payment_intent_id:
            return self.payment
        return None

    async def update_collected(self, transaction_id, collected_by, amount, collected_at):
        self.payment.status = PaymentStatus.COLLECTED
        self.payment.collected_by = collected_by
        self.payment.amount = amount
        self.payment.collected_at = collected_at
        return self.payment

    async def mark_external_status(self, transaction_id, status, provider_status, paid_at, next_action=KEEP):
        self.payment.status = status
        self.payment.provider_status = provider_status
        self.payment.paid_at = paid_at
        if next_action is not KEEP:
            self.payment.provider_next_action = next_action
        return self.payment

    async def list_stale_transactions(self, *, created_before, created_after, limit):
        if self.payment is None or self.payment.payment_intent_id is None:
            return []
        if self.payment.status not in PENDING_PAYMENT_STATUSES:
            return []
        return [self.payment][:limit]

    async def record_webhook_event(self, *, event_id, payment_intent_id, event_type, business_reference, payload):
        if event_id in self.events:
            return False
        self.events.add(event_id)
        return True

    async def get_or_create_wallet(self, driver_id, *, currency="XOF"):
        from app_base.modules.payment.domain.entities import DriverWallet

        if driver_id not in self.wallets:
            self.wallets[driver_id] = DriverWallet(id=uuid4(), driver_id=driver_id, currency=currency)
        return self.wallets[driver_id]

    async def list_ledger_entries(self, driver_id, *, page=1, page_size=20):
        entries = [entry for entry in self.ledger if entry.driver_id == driver_id]
        return entries[(page - 1) * page_size : page * page_size], len(entries)

    async def record_ledger_entry_once(self, entry):
        for existing in self.ledger:
            if (
                existing.driver_id == entry.driver_id
                and existing.entry_type == entry.entry_type
                and existing.reference_type == entry.reference_type
                and existing.reference_id == entry.reference_id
            ):
                return None
        wallet = await self.get_or_create_wallet(entry.driver_id, currency=entry.currency)
        if entry.direction is WalletEntryDirection.CREDIT:
            wallet.balance += entry.amount
        else:
            wallet.balance -= entry.amount
        self.ledger.append(entry)
        return entry

    async def save_topup(self, topup):
        self.topups[topup.id] = topup
        return topup

    async def find_topup_by_id(self, topup_id):
        return self.topups.get(topup_id)

    async def find_topup_by_payment_intent_id(self, payment_intent_id):
        for topup in self.topups.values():
            if topup.payment_intent_id == payment_intent_id:
                return topup
        return None

    async def mark_topup_status(self, topup_id, status, provider_status, paid_at, next_action=KEEP):
        topup = self.topups[topup_id]
        topup.status = status
        topup.provider_status = provider_status
        topup.paid_at = paid_at
        if next_action is not KEEP:
            topup.provider_next_action = next_action
        return topup

    async def list_stale_topups(self, *, created_before, created_after, limit):
        pending = [
            topup
            for topup in self.topups.values()
            if topup.payment_intent_id is not None and topup.status in PENDING_TOPUP_STATUSES
        ]
        return pending[:limit]


class FakeRideRepo:
    def __init__(self, ride):
        self.ride = ride

    async def find_by_id(self, ride_id):
        return self.ride if self.ride.id == ride_id else None


class FakeDriverRepo:
    def __init__(self, driver_id: UUID, user_id: UUID) -> None:
        self.driver_id = driver_id
        self.user_id = user_id

    async def find_by_user_id(self, user_id):
        if user_id != self.user_id:
            return None
        return type("DriverProfile", (), {"id": self.driver_id})()


CHECKOUT_ACTION = {"type": "redirect", "url": "https://checkout.paystack.com/test"}


class FakeDiddiPay:
    """Stand-in for DiddiPay: records what was created, serves what is read.

    `read_status` / `read_next_action` model what the provider reports on
    GET — that is what reconciliation trusts, and it may differ from whatever
    DiddiGo stored at creation time.
    """

    def __init__(
        self,
        intent_id: UUID,
        *,
        read_status: str = "requires_action",
        read_next_action: dict | None = CHECKOUT_ACTION,
        read_amount: int | None = None,
        read_currency: str = "XOF",
        known: bool = True,
    ):
        self.intent_id = intent_id
        self.last_payload = None
        self.last_idempotency_key = None
        self.read_status = read_status
        self.read_next_action = read_next_action
        self.read_amount = read_amount
        self.read_currency = read_currency
        self.known = known
        self.reads: list[str] = []

    async def create_payment_intent(self, payload, *, idempotency_key):
        self.last_payload = payload
        self.last_idempotency_key = idempotency_key
        if self.read_amount is None:
            self.read_amount = payload["amount"]
        return {
            "id": str(self.intent_id),
            "amount": payload["amount"],
            "currency": "XOF",
            "status": "requires_action",
            "attempts": [{"next_action": dict(CHECKOUT_ACTION)}],
        }

    async def get_payment_intent(self, payment_intent_id):
        self.reads.append(str(payment_intent_id))
        if not self.known:
            return None
        attempts = [{"next_action": self.read_next_action}] if self.read_next_action is not None else []
        return {
            "id": str(payment_intent_id),
            "amount": self.read_amount,
            "currency": self.read_currency,
            "status": self.read_status,
            "business_reference": self.last_payload["business_reference"] if self.last_payload else None,
            "attempts": attempts,
        }


def make_completed_ride() -> Ride:
    return Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        status=RideStatus.COMPLETED,
        pickup_location=GeoPoint(lat=5.35, lng=-4.01),
        dropoff_location=GeoPoint(lat=5.36, lng=-4.02),
        estimated_fare=Decimal("3100"),
        final_fare=Decimal("3100"),
        currency="XOF",
        payment_method=RidePaymentMethod.WAVE,
        driver_id=uuid4(),
        platform_commission=Decimal("248"),
        driver_payout_estimate=Decimal("2852"),
    )


@pytest.mark.asyncio
async def test_prepare_wave_creates_diddipay_intent() -> None:
    ride = make_completed_ride()
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id)
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=gateway)

    payload = await service.prepare_payment(
        ride.id,
        "wave",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
        customer_phone="+2250700000000",
    )

    assert payload["status"] == "requires_action"
    assert payload["provider"] == "diddipay"
    assert payload["payment_intent_id"] == str(intent_id)
    assert payload["next_action"]["type"] == "redirect"
    assert gateway.last_idempotency_key == f"diddigo:ride:{ride.id}:collection:v1"
    assert gateway.last_payload["business_reference"] == f"diddigo:ride:{ride.id}"
    assert gateway.last_payload["network"] == "wave"


@pytest.mark.asyncio
async def test_prepare_diddipay_requires_email() -> None:
    ride = make_completed_ride()
    service = PaymentService(
        payment_repo=FakePaymentRepo(),
        ride_repo=FakeRideRepo(ride),
        diddipay=FakeDiddiPay(uuid4()),
    )

    with pytest.raises(ApiError) as exc_info:
        await service.prepare_payment(ride.id, "wave", payer_user_id=ride.passenger_user_id)

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "PAYMENT_EMAIL_REQUIRED"


@pytest.mark.asyncio
async def test_diddipay_webhook_marks_payment_succeeded(monkeypatch) -> None:
    ride = make_completed_ride()
    intent_id = uuid4()
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=FakeDiddiPay(intent_id))
    await service.prepare_payment(
        ride.id,
        "wave",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
    )

    monkeypatch.setattr("app_base.modules.payment.application.services.settings.diddipay_callback_secret", "secret")
    body = {
        "id": "evt_1",
        "type": "payment.succeeded",
        "occurred_at": datetime.now(UTC).isoformat(),
        "data": {
            "payment_intent_id": str(intent_id),
            "business_reference": f"diddigo:ride:{ride.id}",
            "amount": 3100,
            "currency": "XOF",
            "status": "succeeded",
        },
    }
    raw = json.dumps(body, separators=(",", ":")).encode()
    signature = hmac.new(b"secret", raw, hashlib.sha256).hexdigest()

    result = await service.apply_diddipay_webhook(
        raw_body=raw,
        event_id_header="evt_1",
        signature=signature,
    )
    duplicate = await service.apply_diddipay_webhook(
        raw_body=raw,
        event_id_header="evt_1",
        signature=signature,
    )

    assert result["status"] == "processed"
    assert duplicate["status"] == "duplicate"
    assert repo.payment.status is PaymentStatus.SUCCEEDED
    assert repo.payment.paid_at is not None


@pytest.mark.asyncio
async def test_cash_confirmation_debits_driver_commission_once() -> None:
    ride = make_completed_ride()
    ride.payment_method = RidePaymentMethod.CASH
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=FakeDiddiPay(uuid4()))

    await service.confirm_cash(ride.id, Decimal("3100"), collected_by=ride.driver_id)
    await service.confirm_cash(ride.id, Decimal("3100"), collected_by=ride.driver_id)

    assert len(repo.ledger) == 1
    assert repo.ledger[0].entry_type is WalletEntryType.PLATFORM_COMMISSION
    assert repo.ledger[0].direction is WalletEntryDirection.DEBIT
    assert repo.wallets[ride.driver_id].balance == Decimal("-248")


@pytest.mark.asyncio
async def test_digital_payment_webhook_credits_driver_payout_once(monkeypatch) -> None:
    ride = make_completed_ride()
    intent_id = uuid4()
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=FakeDiddiPay(intent_id))
    await service.prepare_payment(
        ride.id,
        "wave",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
    )

    monkeypatch.setattr("app_base.modules.payment.application.services.settings.diddipay_callback_secret", "secret")
    body = {
        "id": "evt_driver_payout",
        "type": "payment.succeeded",
        "occurred_at": datetime.now(UTC).isoformat(),
        "data": {
            "payment_intent_id": str(intent_id),
            "business_reference": f"diddigo:ride:{ride.id}",
            "amount": 3100,
            "currency": "XOF",
            "status": "succeeded",
        },
    }
    raw = json.dumps(body, separators=(",", ":")).encode()
    signature = hmac.new(b"secret", raw, hashlib.sha256).hexdigest()

    await service.apply_diddipay_webhook(raw_body=raw, event_id_header="evt_driver_payout", signature=signature)
    await service.apply_diddipay_webhook(raw_body=raw, event_id_header="evt_driver_payout", signature=signature)

    assert len(repo.ledger) == 1
    assert repo.ledger[0].entry_type is WalletEntryType.RIDE_PAYOUT
    assert repo.ledger[0].direction is WalletEntryDirection.CREDIT
    assert repo.wallets[ride.driver_id].balance == Decimal("2852")


@pytest.mark.asyncio
async def test_driver_topup_callback_credits_wallet_once(monkeypatch) -> None:
    user_id = uuid4()
    driver_id = uuid4()
    intent_id = uuid4()
    repo = FakePaymentRepo()
    wallet_service = DriverWalletService(
        payment_repo=repo,
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=FakeDiddiPay(intent_id),
    )
    payment_service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(make_completed_ride()))
    topup = await wallet_service.create_topup(
        driver_user_id=user_id,
        amount=Decimal("5000"),
        method="wave",
        customer_email="driver@example.com",
    )

    monkeypatch.setattr("app_base.modules.payment.application.services.settings.diddipay_callback_secret", "secret")
    body = {
        "id": "evt_topup",
        "type": "payment.succeeded",
        "occurred_at": datetime.now(UTC).isoformat(),
        "data": {
            "payment_intent_id": topup["payment_intent_id"],
            "business_reference": topup["business_reference"],
            "amount": 5000,
            "currency": "XOF",
            "status": "succeeded",
        },
    }
    raw = json.dumps(body, separators=(",", ":")).encode()
    signature = hmac.new(b"secret", raw, hashlib.sha256).hexdigest()

    await payment_service.apply_diddipay_webhook(raw_body=raw, event_id_header="evt_topup", signature=signature)
    await payment_service.apply_diddipay_webhook(raw_body=raw, event_id_header="evt_topup", signature=signature)

    assert len(repo.ledger) == 1
    assert repo.ledger[0].entry_type is WalletEntryType.TOPUP
    assert repo.wallets[driver_id].balance == Decimal("5000")


@pytest.mark.asyncio
async def test_driver_topup_get_keeps_checkout_next_action() -> None:
    user_id = uuid4()
    driver_id = uuid4()
    wallet_service = DriverWalletService(
        payment_repo=FakePaymentRepo(),
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=FakeDiddiPay(uuid4()),
    )

    created = await wallet_service.create_topup(
        driver_user_id=user_id,
        amount=Decimal("4500"),
        method="diddipay",
        customer_email="driver@example.com",
    )
    fetched = await wallet_service.get_topup(driver_user_id=user_id, topup_id=UUID(created["id"]))

    assert created["next_action"] == CHECKOUT_ACTION
    assert fetched["next_action"] == CHECKOUT_ACTION
