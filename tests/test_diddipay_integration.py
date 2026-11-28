from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app_base.core.errors import ApiError
from app_base.modules.payment.application.services import PaymentService, _payment_status_from_diddipay
from app_base.modules.payment.application.wallet_service import DriverWalletService
from app_base.modules.payment.domain.entities import (
    KEEP,
    PENDING_PAYMENT_STATUSES,
    PENDING_TOPUP_STATUSES,
    PassengerDebt,
    PassengerDebtStatus,
    PaymentStatus,
    Transaction,
    WalletEntryDirection,
    WalletEntryType,
)
from app_base.modules.payment.domain.entities import (
    PaymentMethod as PaymentDomainMethod,
)
from app_base.modules.payment.presentation.schemas import DriverTopupRequest, PaymentPreparationRequest
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
        self.debts = {}
        self.rewards_events = []

    async def find_open_debt_for_passenger(self, passenger_user_id):
        return next(
            (
                debt
                for debt in self.debts.values()
                if debt.passenger_user_id == passenger_user_id and debt.status is not PassengerDebtStatus.SETTLED
            ),
            None,
        )

    async def find_debt_by_id(self, debt_id):
        return self.debts.get(debt_id)

    async def find_debt_by_ride_id(self, ride_id):
        return next((debt for debt in self.debts.values() if debt.ride_id == ride_id), None)

    async def list_debts_for_passenger(self, passenger_user_id, *, page=1, page_size=20):
        debts = [debt for debt in self.debts.values() if debt.passenger_user_id == passenger_user_id]
        return debts[(page - 1) * page_size : page * page_size], len(debts)

    async def save_debt(self, debt):
        self.debts[debt.id] = debt
        return debt

    async def update_debt_status(self, debt_id, *, status, settled_at=None, settled_by=None):
        debt = self.debts[debt_id]
        debt.status = status
        debt.settled_at = settled_at
        debt.settled_by = settled_by
        return debt

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
        self.payment.method = PaymentDomainMethod.CASH
        self.payment.status = PaymentStatus.COLLECTED
        self.payment.collected_by = collected_by
        self.payment.amount = amount
        self.payment.collected_at = collected_at
        return self.payment

    async def prepare_cash_payment(self, transaction_id):
        assert self.payment.id == transaction_id
        self.payment.method = PaymentDomainMethod.CASH
        self.payment.status = PaymentStatus.PENDING
        self.payment.payment_intent_id = None
        self.payment.business_reference = None
        self.payment.idempotency_key = None
        self.payment.provider_status = "local"
        self.payment.provider_next_action = None
        self.payment.paid_at = None
        return self.payment

    async def mark_external_status(self, transaction_id, status, provider_status, paid_at, next_action=KEEP):
        self.payment.status = status
        self.payment.provider_status = provider_status
        self.payment.paid_at = paid_at
        if next_action is not KEEP:
            self.payment.provider_next_action = next_action
        return self.payment

    async def replace_external_intent(
        self,
        transaction_id,
        *,
        payment_intent_id,
        idempotency_key,
        method,
        status,
        provider_status,
        next_action,
    ):
        assert self.payment.id == transaction_id
        self.payment.payment_intent_id = payment_intent_id
        self.payment.idempotency_key = idempotency_key
        self.payment.method = method
        self.payment.status = status
        self.payment.provider_status = provider_status
        self.payment.provider_next_action = next_action
        self.payment.paid_at = None
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

    async def enqueue_rewards_event(self, *, event_type, ride_id, payload):
        self.rewards_events.append({"event_type": event_type, "ride_id": ride_id, "payload": payload})
        return payload["fact_id"]

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


class FakeReturnContexts:
    def __init__(self) -> None:
        self.created: dict | None = None
        self.bound = None

    async def create(self, **kwargs) -> str:
        self.created = kwargs
        return "opaque-context"

    async def bind_payment_intent(self, token, payment_intent_id) -> None:
        self.bound = (token, payment_intent_id)

    @staticmethod
    def callback_url(base_url, token):
        return f"{base_url}?context={token}"


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


class FakeRewardsReconciliation:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def reconciliation(self, **kwargs):
        self.calls.append(kwargs)
        return {"status": "matched"}


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
        payment_method=RidePaymentMethod.MOBILE_MONEY,
        driver_id=uuid4(),
        platform_commission=Decimal("248"),
        driver_payout_estimate=Decimal("2852"),
    )


@pytest.mark.asyncio
async def test_paid_ride_queues_an_order_paid_fact() -> None:
    """Facts protocol v1 (ticket 069): every paid ride, discount or not, total before discount."""
    ride = make_completed_ride()
    ride.rewards_reservation_id = uuid4()
    ride.rewards_discount_amount = Decimal("246")
    driver_user_id = uuid4()
    ride_repo = FakeRideRepo(ride)
    ride_repo.driver_user_id = lambda _profile_id: _async_value(driver_user_id)
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=ride_repo)
    payment = Transaction(
        id=uuid4(),
        ride_id=ride.id,
        amount=Decimal("2854"),
        currency="XOF",
        method=PaymentDomainMethod.MOBILE_MONEY,
        status=PaymentStatus.SUCCEEDED,
    )

    await service._enqueue_rewards_event(ride, payment)

    event = repo.rewards_events[0]
    fact = event["payload"]
    assert event["event_type"] == "order.paid"
    assert fact["fact_id"] == f"diddigo:order.paid:{ride.id}"
    assert fact["schema_version"] == "1"
    assert fact["customer_id"] == str(ride.passenger_user_id)
    assert fact["amount_minor"] == 3100 and fact["discount_minor"] == 246
    assert fact["payment_method"] == "online"
    assert fact["professional_id"] == str(driver_user_id)
    assert fact["rewards_reservation_id"] == str(ride.rewards_reservation_id)
    assert fact["occurred_at"].endswith("Z")


@pytest.mark.asyncio
async def test_ride_without_discount_is_reported_too_and_refund_and_cancel_have_their_facts() -> None:
    ride = make_completed_ride()
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride))
    base = dict(ride_id=ride.id, amount=Decimal("3100"), currency="XOF", method=PaymentDomainMethod.CASH)

    await service._enqueue_rewards_event(ride, Transaction(id=uuid4(), status=PaymentStatus.COLLECTED, **base))
    await service._enqueue_rewards_event(ride, Transaction(id=uuid4(), status=PaymentStatus.REFUNDED, **base))
    await service._enqueue_rewards_event(
        ride, Transaction(id=uuid4(), status=PaymentStatus.PARTIALLY_REFUNDED, **base)
    )
    await service._enqueue_rewards_event(ride, Transaction(id=uuid4(), status=PaymentStatus.CANCELLED, **base))
    await service._enqueue_rewards_event(ride, Transaction(id=uuid4(), status=PaymentStatus.PENDING, **base))

    facts = [event["payload"] for event in repo.rewards_events]
    assert [fact["type"] for fact in facts] == ["order.paid", "order.refunded", "order.cancelled"]
    assert facts[0]["discount_minor"] == 0 and facts[0]["payment_method"] == "cash"
    assert facts[0]["professional_id"] is None  # fake repo cannot resolve the driver
    assert facts[1]["full"] is True and facts[1]["refunded_amount_minor"] == 3100


async def _async_value(value):
    return value


@pytest.mark.asyncio
async def test_successful_payment_triggers_rewards_reconciliation() -> None:
    ride = make_completed_ride()
    ride.rewards_reservation_id = uuid4()
    ride.rewards_consumption_id = uuid4()
    ride.rewards_discount_amount = Decimal("246")
    ride.rewards_status = "confirmed"
    repo = FakePaymentRepo()
    rewards = FakeRewardsReconciliation()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddirewards=rewards)
    payment = Transaction(
        id=uuid4(),
        ride_id=ride.id,
        amount=Decimal("2854"),
        currency="XOF",
        method=PaymentDomainMethod.MOBILE_MONEY,
        status=PaymentStatus.PROCESSING,
    )
    await repo.save(payment)

    await service._apply_transaction_status(
        payment,
        status=PaymentStatus.SUCCEEDED,
        provider_status="succeeded",
        paid_at=datetime.now(UTC),
    )

    assert len(rewards.calls) == 1
    assert rewards.calls[0]["consumption_id"] == ride.rewards_consumption_id
    assert rewards.calls[0]["idempotency_key"] == f"diddigo:ride:{ride.id}:rewards-reconciliation:v1"


@pytest.mark.asyncio
@pytest.mark.parametrize("network", ["wave", "moov"])
async def test_prepare_mobile_money_creates_diddipay_intent(monkeypatch, network: str) -> None:
    monkeypatch.setattr(
        "app_base.modules.payment.application.services.settings.diddigo_consumer_return_url",
        "https://go.test/payments/return",
    )
    ride = make_completed_ride()
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id)
    repo = FakePaymentRepo()
    contexts = FakeReturnContexts()
    service = PaymentService(
        payment_repo=repo,
        ride_repo=FakeRideRepo(ride),
        diddipay=gateway,
        return_contexts=contexts,  # type: ignore[arg-type]
    )

    payload = await service.prepare_payment(
        ride.id,
        "mobile_money",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
        customer_phone="+2250700000000",
        mobile_money_network=network,
    )

    assert payload["status"] == "requires_action"
    assert payload["provider"] == "diddipay"
    assert payload["payment_intent_id"] == str(intent_id)
    assert payload["next_action"]["type"] == "redirect"
    assert gateway.last_idempotency_key == f"diddigo:ride:{ride.id}:collection:v1"
    assert gateway.last_payload["business_reference"] == f"diddigo:ride:{ride.id}"
    assert gateway.last_payload["network"] == network
    assert gateway.last_payload["callback_url"] == "https://go.test/payments/return?context=opaque-context"
    assert contexts.created == {
        "flow": "ride_payment",
        "surface": "consumer",
        "user_id": ride.passenger_user_id,
        "resource_id": ride.id,
    }
    assert contexts.bound == ("opaque-context", intent_id)


@pytest.mark.asyncio
async def test_prepare_payment_rejects_ride_before_completion() -> None:
    ride = make_completed_ride()
    ride.status = RideStatus.IN_PROGRESS
    gateway = FakeDiddiPay(uuid4())
    service = PaymentService(
        payment_repo=FakePaymentRepo(),
        ride_repo=FakeRideRepo(ride),
        diddipay=gateway,
    )

    with pytest.raises(ApiError) as exc_info:
        await service.prepare_payment(
            ride.id,
            "mobile_money",
            payer_user_id=ride.passenger_user_id,
            customer_email="client@example.com",
            mobile_money_network="wave",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "RIDE_NOT_COMPLETED"
    assert exc_info.value.details == {"ride_status": "in_progress"}
    assert gateway.last_payload is None


@pytest.mark.asyncio
async def test_prepare_wave_replaces_failed_intent_and_then_reuses_retry(monkeypatch) -> None:
    monkeypatch.setattr(
        "app_base.modules.payment.application.services.settings.diddigo_consumer_return_url",
        "https://go.test/payments/return",
    )
    ride = make_completed_ride()
    failed_intent_id = uuid4()
    retry_intent_id = uuid4()
    repo = FakePaymentRepo()
    repo.payment = Transaction(
        id=uuid4(),
        ride_id=ride.id,
        amount=ride.final_fare,
        method=PaymentDomainMethod.MOBILE_MONEY,
        status=PaymentStatus.FAILED,
        payment_intent_id=failed_intent_id,
        idempotency_key=f"diddigo:ride:{ride.id}:collection:v1",
        provider_status="failed",
    )
    gateway = FakeDiddiPay(retry_intent_id)
    service = PaymentService(
        payment_repo=repo,
        ride_repo=FakeRideRepo(ride),
        diddipay=gateway,
        return_contexts=FakeReturnContexts(),  # type: ignore[arg-type]
    )

    retried = await service.prepare_payment(
        ride.id,
        "mobile_money",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
        mobile_money_network="wave",
        customer_phone="+2250707000000",
    )
    reused = await service.prepare_payment(
        ride.id,
        "mobile_money",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
        mobile_money_network="wave",
        customer_phone="+2250707000000",
    )

    assert retried["payment_intent_id"] == str(retry_intent_id)
    assert retried["status"] == "requires_action"
    assert reused["payment_intent_id"] == str(retry_intent_id)
    assert gateway.last_idempotency_key == (f"diddigo:ride:{ride.id}:collection:retry:{failed_intent_id}")


@pytest.mark.asyncio
async def test_failed_mobile_money_can_switch_to_cash_for_same_completed_ride() -> None:
    ride = make_completed_ride()
    repo = FakePaymentRepo()
    repo.payment = Transaction(
        id=uuid4(),
        ride_id=ride.id,
        amount=ride.final_fare,
        method=PaymentDomainMethod.MOBILE_MONEY,
        status=PaymentStatus.FAILED,
        payment_intent_id=uuid4(),
        provider_status="failed",
    )
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride))

    result = await service.prepare_payment(
        ride.id,
        "cash",
        payer_user_id=ride.passenger_user_id,
    )

    assert result["method"] == "cash"
    assert result["status"] == "pending"
    assert repo.payment.method is PaymentDomainMethod.CASH
    assert repo.payment.payment_intent_id is None

    confirmed = await service.confirm_cash(
        ride.id,
        Decimal("3100"),
        collected_by=ride.driver_id,
    )

    assert confirmed["status"] == "collected"
    assert repo.payment.method is PaymentDomainMethod.CASH


@pytest.mark.asyncio
async def test_failed_mobile_money_for_completed_ride_does_not_open_passenger_debt() -> None:
    ride = make_completed_ride()
    repo = FakePaymentRepo()
    payment = Transaction(
        id=uuid4(),
        ride_id=ride.id,
        amount=ride.final_fare,
        method=PaymentDomainMethod.MOBILE_MONEY,
        status=PaymentStatus.PROCESSING,
    )
    await repo.save(payment)
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride))

    await service._apply_transaction_status(
        payment,
        status=PaymentStatus.FAILED,
        provider_status="failed",
        paid_at=None,
    )

    debt = await repo.find_debt_by_ride_id(ride.id)
    assert debt is None


@pytest.mark.asyncio
async def test_successful_ride_payment_does_not_mutate_legacy_passenger_debt() -> None:
    ride = make_completed_ride()
    repo = FakePaymentRepo()
    debt = PassengerDebt(
        id=uuid4(),
        passenger_user_id=ride.passenger_user_id,
        ride_id=ride.id,
        amount=Decimal("3100"),
        status=PassengerDebtStatus.MOBILE_MONEY_PENDING,
    )
    await repo.save_debt(debt)
    payment = Transaction(
        id=uuid4(),
        ride_id=ride.id,
        amount=Decimal("3100"),
        method=PaymentDomainMethod.MOBILE_MONEY,
        status=PaymentStatus.PROCESSING,
    )
    await repo.save(payment)
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride))

    await service._apply_transaction_status(
        payment,
        status=PaymentStatus.SUCCEEDED,
        provider_status="succeeded",
        paid_at=datetime.now(UTC),
    )

    assert (await repo.find_debt_by_id(debt.id)).status is PassengerDebtStatus.MOBILE_MONEY_PENDING


def test_payment_requests_reject_client_owned_callback_urls() -> None:
    with pytest.raises(ValidationError):
        PaymentPreparationRequest(
            method="mobile_money",
            mobile_money_network="wave",
            callback_url="https://attacker.test/redirect",
        )


def test_payment_request_accepts_moov_mobile_money_network() -> None:
    payload = PaymentPreparationRequest(method="mobile_money", mobile_money_network="moov")

    assert payload.mobile_money_network == "moov"

    with pytest.raises(ValidationError):
        DriverTopupRequest(
            amount=5000,
            customer_email="driver@example.com",
            callback_url="https://attacker.test/redirect",
        )


def test_expired_diddipay_intent_is_a_retryable_terminal_status() -> None:
    assert _payment_status_from_diddipay("expired") is PaymentStatus.CANCELLED


@pytest.mark.asyncio
async def test_prepare_mobile_money_without_any_phone_or_email_asks_for_the_phone() -> None:
    """Without a number to charge, the phone is asked first (PawaPay cannot charge without it;
    with a phone, a missing email is derived from it, so PAYMENT_EMAIL_REQUIRED cannot happen)."""
    ride = make_completed_ride()
    service = PaymentService(
        payment_repo=FakePaymentRepo(),
        ride_repo=FakeRideRepo(ride),
        diddipay=FakeDiddiPay(uuid4()),
    )

    with pytest.raises(ApiError) as exc_info:
        await service.prepare_payment(
            ride.id,
            "mobile_money",
            payer_user_id=ride.passenger_user_id,
            mobile_money_network="wave",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.details == {"field": "customer_phone"}


@pytest.mark.asyncio
async def test_diddipay_webhook_marks_payment_succeeded(monkeypatch) -> None:
    ride = make_completed_ride()
    intent_id = uuid4()
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=FakeDiddiPay(intent_id))
    await service.prepare_payment(
        ride.id,
        "mobile_money",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
        mobile_money_network="wave",
        customer_phone="+2250707000000",
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
async def test_cash_ride_with_discount_credits_the_discount_to_the_driver_once() -> None:
    """Ticket 039 / decision D6: DiddiFree pays the discount, the driver gets the full price.

    Staging ride fd8257d4: price 1234, commission 222, driver share 1012, discount 246. The passenger
    hands over 988 in cash; the wallet must move by -222 + 246 = +24 so the driver ends with 1012.
    """
    ride = make_completed_ride()
    ride.payment_method = RidePaymentMethod.CASH
    ride.estimated_fare = ride.final_fare = Decimal("1234")
    ride.platform_commission = Decimal("222")
    ride.driver_payout_estimate = Decimal("1012")
    ride.rewards_discount_amount = Decimal("246")
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=FakeDiddiPay(uuid4()))

    await service.confirm_cash(ride.id, Decimal("988"), collected_by=ride.driver_id)
    await service.confirm_cash(ride.id, Decimal("988"), collected_by=ride.driver_id)

    by_type = {entry.entry_type: entry for entry in repo.ledger}
    assert set(by_type) == {WalletEntryType.PLATFORM_COMMISSION, WalletEntryType.REWARDS_DISCOUNT}
    assert len(repo.ledger) == 2
    credit = by_type[WalletEntryType.REWARDS_DISCOUNT]
    assert credit.direction is WalletEntryDirection.CREDIT
    assert credit.amount == Decimal("246")
    assert (credit.reference_type, credit.reference_id) == ("ride", ride.id)
    assert repo.wallets[ride.driver_id].balance == Decimal("24")
    cash_in_hand = Decimal("988")
    assert cash_in_hand + repo.wallets[ride.driver_id].balance == ride.driver_payout_estimate


@pytest.mark.asyncio
async def test_cash_ride_with_zero_discount_gets_no_discount_credit() -> None:
    ride = make_completed_ride()
    ride.payment_method = RidePaymentMethod.CASH
    ride.rewards_reservation_id = uuid4()
    ride.rewards_discount_amount = Decimal("0")
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=FakeDiddiPay(uuid4()))

    await service.confirm_cash(ride.id, Decimal("3100"), collected_by=ride.driver_id)

    assert [entry.entry_type for entry in repo.ledger] == [WalletEntryType.PLATFORM_COMMISSION]


@pytest.mark.asyncio
async def test_driver_wallet_blocks_online_when_balance_is_below_minimum(monkeypatch) -> None:
    user_id = uuid4()
    driver_id = uuid4()
    repo = FakePaymentRepo()
    wallet = await repo.get_or_create_wallet(driver_id)
    wallet.balance = Decimal("-1")
    service = DriverWalletService(
        payment_repo=repo,
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
    )
    monkeypatch.setattr("app_base.modules.payment.application.wallet_service.settings.driver_min_balance", 0)

    with pytest.raises(ApiError) as exc_info:
        await service.ensure_driver_can_go_online(driver_id)

    assert exc_info.value.code == "DRIVER_BALANCE_TOO_LOW"
    assert exc_info.value.details == {"balance": -1, "min_balance": 0, "currency": "XOF"}


@pytest.mark.asyncio
async def test_digital_payment_webhook_credits_driver_payout_once(monkeypatch) -> None:
    ride = make_completed_ride()
    intent_id = uuid4()
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=FakeDiddiPay(intent_id))
    await service.prepare_payment(
        ride.id,
        "mobile_money",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
        mobile_money_network="wave",
        customer_phone="+2250707000000",
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
    monkeypatch.setattr(
        "app_base.modules.payment.application.wallet_service.settings.diddigo_pro_return_url",
        "https://go.test/wallet/return",
    )
    user_id = uuid4()
    driver_id = uuid4()
    intent_id = uuid4()
    repo = FakePaymentRepo()
    gateway = FakeDiddiPay(intent_id)
    contexts = FakeReturnContexts()
    wallet_service = DriverWalletService(
        payment_repo=repo,
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=gateway,
        return_contexts=contexts,  # type: ignore[arg-type]
    )
    payment_service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(make_completed_ride()))
    topup = await wallet_service.create_topup(
        driver_user_id=user_id,
        amount=Decimal("5000"),
        method="wave",
        customer_email="driver@example.com",
        customer_phone="+2250707000000",
    )
    assert gateway.last_payload["callback_url"] == "https://go.test/wallet/return?context=opaque-context"
    assert contexts.created == {
        "flow": "driver_topup",
        "surface": "pro",
        "user_id": user_id,
        "resource_id": UUID(topup["id"]),
    }
    assert contexts.bound == ("opaque-context", intent_id)

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
        mobile_money_network="orange",
        customer_phone="+2250707000000",
    )
    fetched = await wallet_service.get_topup(driver_user_id=user_id, topup_id=UUID(created["id"]))

    assert created["next_action"] == CHECKOUT_ACTION
    assert fetched["next_action"] == CHECKOUT_ACTION


@pytest.mark.asyncio
@pytest.mark.parametrize("network", ["orange", "mtn", "moov", "wave"])
async def test_driver_topup_sends_the_chosen_mobile_money_network(network) -> None:
    """A top-up must name the operator to charge (PawaPay refused network=None)."""
    user_id, driver_id = uuid4(), uuid4()
    gateway = FakeDiddiPay(uuid4())
    wallet_service = DriverWalletService(
        payment_repo=FakePaymentRepo(),
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=gateway,
    )
    await wallet_service.create_topup(
        driver_user_id=user_id, amount=Decimal("15000"), method="mobile_money",
        customer_email="driver@example.com", mobile_money_network=network, customer_phone="+2250707000000",
    )
    assert gateway.last_payload["network"] == network
    assert gateway.last_payload["channel"] == "mobile_money"


@pytest.mark.asyncio
async def test_old_wave_topup_method_still_sends_wave() -> None:
    user_id, driver_id = uuid4(), uuid4()
    gateway = FakeDiddiPay(uuid4())
    wallet_service = DriverWalletService(
        payment_repo=FakePaymentRepo(),
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=gateway,
    )
    await wallet_service.create_topup(
        driver_user_id=user_id, amount=Decimal("15000"), method="wave", customer_email="driver@example.com",
        customer_phone="+2250707000000",
    )
    assert gateway.last_payload["network"] == "wave"


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["diddipay", "mobile_money"])
async def test_topup_without_network_is_refused_before_anything_is_created(method) -> None:
    user_id, driver_id = uuid4(), uuid4()
    repo = FakePaymentRepo()
    gateway = FakeDiddiPay(uuid4())
    wallet_service = DriverWalletService(
        payment_repo=repo,
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=gateway,
    )
    with pytest.raises(ApiError) as excinfo:
        await wallet_service.create_topup(
            driver_user_id=user_id, amount=Decimal("15000"), method=method, customer_email="driver@example.com",
        )
    assert excinfo.value.status_code == 422
    assert excinfo.value.details == {"field": "mobile_money_network", "allowed": ["orange", "wave", "mtn", "moov"]}
    assert repo.topups == {}
    assert getattr(gateway, "last_payload", None) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("phone", [None, "", "   ", "+000123456789012"])
async def test_wave_topup_without_a_real_phone_is_refused_before_anything_is_created(phone) -> None:
    """PawaPay needs the mobile money number to charge ('customer_phone is required')."""
    user_id, driver_id = uuid4(), uuid4()
    repo = FakePaymentRepo()
    gateway = FakeDiddiPay(uuid4())
    wallet_service = DriverWalletService(
        payment_repo=repo,
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=gateway,
    )
    with pytest.raises(ApiError) as excinfo:
        await wallet_service.create_topup(
            driver_user_id=user_id, amount=Decimal("15000"), method="mobile_money",
            customer_email="driver@example.com", mobile_money_network="wave", customer_phone=phone,
        )
    assert excinfo.value.status_code == 422
    assert excinfo.value.details == {"field": "customer_phone"}
    assert repo.topups == {}
    assert gateway.last_payload is None


@pytest.mark.asyncio
async def test_topup_sends_the_phone_to_charge() -> None:
    user_id, driver_id = uuid4(), uuid4()
    gateway = FakeDiddiPay(uuid4())
    wallet_service = DriverWalletService(
        payment_repo=FakePaymentRepo(),
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=gateway,
    )
    await wallet_service.create_topup(
        driver_user_id=user_id, amount=Decimal("15000"), method="mobile_money",
        customer_email="driver@example.com", mobile_money_network="mtn", customer_phone=" +2250505000000 ",
    )
    assert gateway.last_payload["customer_phone"] == "+2250505000000"


@pytest.mark.asyncio
@pytest.mark.parametrize("phone", [None, "", "+000123456789012"])
async def test_wave_ride_without_a_real_phone_is_refused_before_anything(phone) -> None:
    ride = make_completed_ride()
    repo = FakePaymentRepo()
    gateway = FakeDiddiPay(uuid4())
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=gateway)
    with pytest.raises(ApiError) as excinfo:
        await service.prepare_payment(
            ride.id, "mobile_money", payer_user_id=ride.passenger_user_id,
            customer_email="client@example.com", mobile_money_network="wave", customer_phone=phone,
        )
    assert excinfo.value.status_code == 422 and excinfo.value.details == {"field": "customer_phone"}
    assert gateway.last_payload is None


@pytest.mark.asyncio
async def test_ride_mobile_money_sends_the_number_chosen_by_the_customer() -> None:
    ride = make_completed_ride()
    gateway = FakeDiddiPay(uuid4())
    service = PaymentService(payment_repo=FakePaymentRepo(), ride_repo=FakeRideRepo(ride), diddipay=gateway)
    await service.prepare_payment(
        ride.id, "mobile_money", payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com", mobile_money_network="mtn", customer_phone=" +2250505000000 ",
    )
    assert gateway.last_payload["customer_phone"] == "+2250505000000"


@pytest.mark.asyncio
async def test_wave_debt_without_a_phone_is_refused_before_anything() -> None:
    ride = make_completed_ride()
    repo = FakePaymentRepo()
    debt = PassengerDebt(id=uuid4(), passenger_user_id=ride.passenger_user_id, ride_id=ride.id, amount=Decimal("3100"))
    repo.debts[debt.id] = debt
    gateway = FakeDiddiPay(uuid4())
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=gateway)
    with pytest.raises(ApiError) as excinfo:
        await service.prepare_passenger_debt_payment(
            debt.id, passenger_user_id=ride.passenger_user_id, customer_email="client@example.com",
            customer_phone=None, mobile_money_network="wave",
        )
    assert excinfo.value.status_code == 422 and excinfo.value.details == {"field": "customer_phone"}
    assert gateway.last_payload is None
    assert repo.debts[debt.id].status is PassengerDebtStatus.OPEN


@pytest.mark.asyncio
@pytest.mark.parametrize("network", ["orange", "mtn", "moov"])
async def test_without_a_number_pawapay_networks_go_to_the_page_with_no_phone(network) -> None:
    """DiddiPay 108: the customer types the number on PawaPay's page."""
    ride = make_completed_ride()
    gateway = FakeDiddiPay(uuid4())
    service = PaymentService(payment_repo=FakePaymentRepo(), ride_repo=FakeRideRepo(ride), diddipay=gateway)
    await service.prepare_payment(
        ride.id, "mobile_money", payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com", mobile_money_network=network, customer_phone="+000123456789012",
    )
    assert gateway.last_payload["customer_phone"] is None
    assert gateway.last_payload["network"] == network

    user_id, driver_id = uuid4(), uuid4()
    topup_gateway = FakeDiddiPay(uuid4())
    await DriverWalletService(
        payment_repo=FakePaymentRepo(),
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=topup_gateway,
    ).create_topup(
        driver_user_id=user_id, amount=Decimal("1000"), method="mobile_money",
        customer_email="driver@example.com", mobile_money_network=network,
    )
    assert topup_gateway.last_payload["customer_phone"] is None


async def _paid_mobile_money_ride(monkeypatch, *, read_status="succeeded"):
    """A mobile money ride paid 3100, driver credited 2852 (make_completed_ride)."""
    ride = make_completed_ride()
    intent_id = uuid4()
    repo = FakePaymentRepo()
    gateway = FakeDiddiPay(intent_id, read_status=read_status)
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=gateway)
    await service.prepare_payment(
        ride.id, "mobile_money", payer_user_id=ride.passenger_user_id, customer_email="client@example.com",
        mobile_money_network="orange", customer_phone="+2250707000000",
    )
    monkeypatch.setattr("app_base.modules.payment.application.services.settings.diddipay_callback_secret", "secret")
    await _send(service, "evt_paid", "payment.succeeded", {
        "payment_intent_id": str(intent_id), "business_reference": f"diddigo:ride:{ride.id}",
        "amount": 3100, "currency": "XOF", "status": "succeeded",
    })
    return ride, intent_id, repo, gateway, service


async def _send(service, event_id, event_type, data):
    raw = json.dumps({"id": event_id, "type": event_type, "occurred_at": datetime.now(UTC).isoformat(),
                      "data": data}, separators=(",", ":")).encode()
    signature = hmac.new(b"secret", raw, hashlib.sha256).hexdigest()
    return await service.apply_diddipay_webhook(raw_body=raw, event_id_header=event_id, signature=signature)


def _refund(intent_id, ride, *, amount, refund_id=None, recover=False, status="succeeded"):
    return {
        "event_version": "1", "refund_id": str(refund_id or uuid4()), "payment_intent_id": str(intent_id),
        "business_reference": f"diddigo:ride:{ride.id}", "amount": amount, "currency": "XOF",
        "status": status, "recover_from_payee": recover,
    }


@pytest.mark.asyncio
async def test_full_refund_event_marks_the_ride_refunded_and_keeps_the_driver_paid(monkeypatch) -> None:
    """Ticket 115: the refund event carries the refund status; DiddiGo re-reads the intent."""
    ride, intent_id, repo, gateway, service = await _paid_mobile_money_ride(monkeypatch)
    paid_balance = sum(e.amount for e in repo.ledger if e.driver_id == ride.driver_id)
    gateway.read_status = "refunded"

    result = await _send(service, "evt_refund", "diddipay.refund.succeeded.v1", _refund(intent_id, ride, amount=3100))

    assert result["reference_type"] == "ride_refund"
    assert repo.payment.status is PaymentStatus.REFUNDED
    assert [e for e in repo.ledger if e.entry_type is WalletEntryType.REFUND] == []
    assert sum(e.amount for e in repo.ledger if e.driver_id == ride.driver_id) == paid_balance
    facts = [event["payload"] for event in repo.rewards_events]
    assert [fact["type"] for fact in facts] == ["order.paid", "order.refunded"]


@pytest.mark.asyncio
async def test_partial_refund_event_is_accepted_not_rejected_for_its_amount(monkeypatch) -> None:
    ride, intent_id, repo, gateway, service = await _paid_mobile_money_ride(monkeypatch)
    gateway.read_status = "partially_refunded"
    result = await _send(service, "evt_part", "diddipay.refund.succeeded.v1", _refund(intent_id, ride, amount=1550))
    assert result["status"] == "processed"
    assert repo.payment.status is PaymentStatus.PARTIALLY_REFUNDED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("refunded", "status", "debited"), [(3100, "refunded", 2852), (1550, "partially_refunded", 1426)]
)
async def test_admin_recovery_debits_the_driver_his_share_once(monkeypatch, refunded, status, debited) -> None:
    """Ticket 125: recover_from_payee -> driver share x refunded / paid, once per refund."""
    ride, intent_id, repo, gateway, service = await _paid_mobile_money_ride(monkeypatch)
    gateway.read_status = status
    refund_id = uuid4()
    data = _refund(intent_id, ride, amount=refunded, refund_id=refund_id, recover=True)

    await _send(service, "evt_r1", "diddipay.refund.succeeded.v1", data)
    await _send(service, "evt_r2", "diddipay.refund.succeeded.v1", data)  # same refund, new event id

    debits = [e for e in repo.ledger if e.entry_type is WalletEntryType.REFUND]
    assert len(debits) == 1
    assert debits[0].amount == Decimal(debited) and debits[0].direction is WalletEntryDirection.DEBIT
    assert debits[0].reference_type == "diddipay_refund" and debits[0].reference_id == refund_id


@pytest.mark.asyncio
async def test_refund_not_finished_changes_nothing(monkeypatch) -> None:
    ride, intent_id, repo, gateway, service = await _paid_mobile_money_ride(monkeypatch)
    gateway.read_status = "succeeded"  # DiddiPay has not applied the refund to the intent yet
    result = await _send(service, "evt_pend", "diddipay.refund.pending.v1",
                         _refund(intent_id, ride, amount=3100, status="pending", recover=True))
    assert result["status"] == "processed"
    assert repo.payment.status is PaymentStatus.SUCCEEDED
    assert [e for e in repo.ledger if e.entry_type is WalletEntryType.REFUND] == []


@pytest.mark.asyncio
async def test_payment_failed_and_cancelled_callbacks_are_applied(monkeypatch) -> None:
    """DiddiPay 122: new event types, same data.status: DiddiGo applies them."""
    for event_type, status, expected in [
        ("payment.failed", "failed", PaymentStatus.FAILED),
        ("payment.cancelled", "cancelled", PaymentStatus.CANCELLED),
    ]:
        ride = make_completed_ride()
        intent_id = uuid4()
        repo = FakePaymentRepo()
        service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=FakeDiddiPay(intent_id))
        await service.prepare_payment(
            ride.id, "mobile_money", payer_user_id=ride.passenger_user_id, customer_email="client@example.com",
            mobile_money_network="mtn", customer_phone="+2250505000000",
        )
        monkeypatch.setattr(
            "app_base.modules.payment.application.services.settings.diddipay_callback_secret", "secret"
        )
        result = await _send(service, f"evt_{status}", event_type, {
            "payment_intent_id": str(intent_id), "business_reference": f"diddigo:ride:{ride.id}",
            "amount": 3100, "currency": "XOF", "status": status, "failure_code": "X", "failure_message": "y",
        })
        assert result["status"] == "processed"
        assert repo.payment.status is expected
