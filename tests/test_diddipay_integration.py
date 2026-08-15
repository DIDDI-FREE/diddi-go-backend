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
from app_base.modules.payment.domain.entities import PaymentStatus
from app_base.modules.ride.domain.entities import PaymentMethod as RidePaymentMethod
from app_base.modules.ride.domain.entities import Ride, RideStatus
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


class FakePaymentRepo:
    def __init__(self) -> None:
        self.payment = None
        self.events: set[str] = set()

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

    async def mark_external_status(self, transaction_id, status, provider_status, paid_at):
        self.payment.status = status
        self.payment.provider_status = provider_status
        self.payment.paid_at = paid_at
        return self.payment

    async def record_webhook_event(self, *, event_id, payment_intent_id, event_type, business_reference, payload):
        if event_id in self.events:
            return False
        self.events.add(event_id)
        return True


class FakeRideRepo:
    def __init__(self, ride):
        self.ride = ride

    async def find_by_id(self, ride_id):
        return self.ride if self.ride.id == ride_id else None


class FakeDiddiPay:
    def __init__(self, intent_id: UUID):
        self.intent_id = intent_id
        self.last_payload = None
        self.last_idempotency_key = None

    async def create_payment_intent(self, payload, *, idempotency_key):
        self.last_payload = payload
        self.last_idempotency_key = idempotency_key
        return {
            "id": str(self.intent_id),
            "amount": payload["amount"],
            "currency": "XOF",
            "status": "requires_action",
            "attempts": [
                {
                    "next_action": {
                        "type": "redirect",
                        "url": "https://checkout.paystack.com/test",
                    }
                }
            ],
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
    assert gateway.last_idempotency_key == f"ride:{ride.id}:collection:v1"
    assert gateway.last_payload["business_reference"] == f"ride:{ride.id}"
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
            "business_reference": f"ride:{ride.id}",
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
