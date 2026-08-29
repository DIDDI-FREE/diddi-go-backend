"""Reconciliation: what happens when the DiddiPay callback never arrives.

Every test here starts from a payment DiddiGo created normally and then simply
never received a webhook for — the failure mode that strands a driver's topup
in `requires_action` while their money has already left their account.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.payment.application.services import PaymentService
from app_base.modules.payment.application.wallet_service import DriverWalletService
from app_base.modules.payment.domain.entities import (
    PaymentStatus,
    TopupStatus,
    WalletEntryDirection,
    WalletEntryType,
)
from tests.test_diddipay_integration import (
    CHECKOUT_ACTION,
    FakeDiddiPay,
    FakeDriverRepo,
    FakePaymentRepo,
    FakeRideRepo,
    make_completed_ride,
)

pytestmark = pytest.mark.unit


async def _pending_topup(repo: FakePaymentRepo, gateway: FakeDiddiPay, *, amount: str = "5000"):
    """Create a topup that stopped at `requires_action`, as a lost callback leaves it."""
    user_id, driver_id = uuid4(), uuid4()
    wallet_service = DriverWalletService(
        payment_repo=repo,
        driver_repo=FakeDriverRepo(driver_id=driver_id, user_id=user_id),
        diddipay=gateway,
    )
    payload = await wallet_service.create_topup(
        driver_user_id=user_id,
        amount=Decimal(amount),
        method="wave",
        customer_email="driver@example.com",
    )
    return driver_id, payload


def _service(repo: FakePaymentRepo, gateway: FakeDiddiPay) -> PaymentService:
    return PaymentService(
        payment_repo=repo,
        ride_repo=FakeRideRepo(make_completed_ride()),
        diddipay=gateway,
    )


@pytest.mark.asyncio
async def test_lost_callback_on_topup_is_repaired_and_credits_the_wallet_once() -> None:
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id)
    repo = FakePaymentRepo()
    driver_id, payload = await _pending_topup(repo, gateway)
    assert payload["status"] == "requires_action"

    # DiddiPay took the money but its callback never reached DiddiGo.
    gateway.read_status = "succeeded"
    gateway.read_next_action = None

    service = _service(repo, gateway)
    report = await service.reconcile_pending(min_age_seconds=0)
    # A second sweep must not double-credit.
    await service.reconcile_pending(min_age_seconds=0)

    topup = repo.topups[list(repo.topups)[0]]
    assert topup.status is TopupStatus.SUCCEEDED
    assert topup.paid_at is not None
    assert report.updated == 1
    assert report.updated_references == [f"diddigo:driver_topup:{topup.id}"]
    assert len(repo.ledger) == 1
    assert repo.ledger[0].entry_type is WalletEntryType.TOPUP
    assert repo.ledger[0].direction is WalletEntryDirection.CREDIT
    assert repo.wallets[driver_id].balance == Decimal("5000")


@pytest.mark.asyncio
async def test_lost_callback_on_ride_payment_settles_the_driver() -> None:
    ride = make_completed_ride()
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id, read_amount=3100)
    repo = FakePaymentRepo()
    service = PaymentService(payment_repo=repo, ride_repo=FakeRideRepo(ride), diddipay=gateway)
    await service.prepare_payment(
        ride.id,
        "wave",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
    )

    gateway.read_status = "succeeded"
    gateway.read_next_action = None

    report = await service.reconcile_pending(min_age_seconds=0)

    assert report.updated == 1
    assert repo.payment.status is PaymentStatus.SUCCEEDED
    assert repo.payment.paid_at is not None
    assert len(repo.ledger) == 1
    assert repo.ledger[0].entry_type is WalletEntryType.RIDE_PAYOUT
    assert repo.wallets[ride.driver_id].balance == Decimal("2852")


@pytest.mark.asyncio
async def test_reconciliation_restores_a_missing_next_action() -> None:
    """A topup created before next_action was persisted still gets its URL back."""
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id)
    repo = FakePaymentRepo()
    await _pending_topup(repo, gateway)
    topup = repo.topups[list(repo.topups)[0]]
    topup.provider_next_action = None  # the pre-fix rows in staging look like this

    report = await _service(repo, gateway).reconcile_pending(min_age_seconds=0)

    assert report.updated == 1
    assert topup.status is TopupStatus.REQUIRES_ACTION
    assert topup.provider_next_action == CHECKOUT_ACTION


@pytest.mark.asyncio
async def test_unchanged_intent_is_not_rewritten() -> None:
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id)
    repo = FakePaymentRepo()
    await _pending_topup(repo, gateway)

    report = await _service(repo, gateway).reconcile_pending(min_age_seconds=0)

    assert report.checked == 1
    assert report.unchanged == 1
    assert report.updated == 0


@pytest.mark.asyncio
async def test_amount_mismatch_is_reported_and_never_applied() -> None:
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id)
    repo = FakePaymentRepo()
    await _pending_topup(repo, gateway, amount="5000")

    # Wrong money: succeeded, but for an amount DiddiGo never asked for.
    gateway.read_status = "succeeded"
    gateway.read_amount = 50_000

    report = await _service(repo, gateway).reconcile_pending(min_age_seconds=0)

    topup = repo.topups[list(repo.topups)[0]]
    assert report.mismatched == 1
    assert report.updated == 0
    assert topup.status is TopupStatus.REQUIRES_ACTION
    assert repo.ledger == []


@pytest.mark.asyncio
async def test_unknown_intent_is_counted_as_missing() -> None:
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id, known=False)
    repo = FakePaymentRepo()
    await _pending_topup(repo, gateway)

    report = await _service(repo, gateway).reconcile_pending(min_age_seconds=0)

    assert report.missing == 1
    assert report.updated == 0
    assert repo.topups[list(repo.topups)[0]].status is TopupStatus.REQUIRES_ACTION


@pytest.mark.asyncio
async def test_provider_error_does_not_abort_the_sweep() -> None:
    """One unreadable intent must not cost the other rows their repair."""
    ride = make_completed_ride()
    ride_gateway = FakeDiddiPay(uuid4(), read_amount=3100)
    topup_gateway = FakeDiddiPay(uuid4(), read_status="succeeded", read_next_action=None, read_amount=5000)
    repo = FakePaymentRepo()

    await PaymentService(
        payment_repo=repo,
        ride_repo=FakeRideRepo(ride),
        diddipay=ride_gateway,
    ).prepare_payment(
        ride.id,
        "wave",
        payer_user_id=ride.passenger_user_id,
        customer_email="client@example.com",
    )
    await _pending_topup(repo, topup_gateway)

    ride_intent_id = str(repo.payment.payment_intent_id)

    class FlakyGateway:
        """DiddiPay is down for the ride's intent, healthy for the topup's."""

        async def get_payment_intent(self, payment_intent_id):
            if str(payment_intent_id) == ride_intent_id:
                raise ApiError(503, "DIDDIPAY_UNAVAILABLE", "DiddiPay est indisponible.")
            return await topup_gateway.get_payment_intent(payment_intent_id)

    service = PaymentService(
        payment_repo=repo,
        ride_repo=FakeRideRepo(ride),
        diddipay=FlakyGateway(),
    )
    report = await service.reconcile_pending(min_age_seconds=0)

    assert report.errors == 1
    assert report.updated == 1  # the topup was still repaired
    assert repo.payment.status is PaymentStatus.REQUIRES_ACTION
    assert repo.topups[list(repo.topups)[0]].status is TopupStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_reconcile_single_topup_targets_only_that_row() -> None:
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id)
    repo = FakePaymentRepo()
    await _pending_topup(repo, gateway)
    topup = repo.topups[list(repo.topups)[0]]
    gateway.read_status = "succeeded"
    gateway.read_next_action = None

    report = await _service(repo, gateway).reconcile_topup(topup.id)

    assert report.checked == 1
    assert report.updated == 1
    assert topup.status is TopupStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_reconcile_single_topup_404s_for_an_unknown_id() -> None:
    service = _service(FakePaymentRepo(), FakeDiddiPay(uuid4()))

    with pytest.raises(ApiError) as exc_info:
        await service.reconcile_topup(uuid4())

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "PAYMENT_INTENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_terminal_payments_are_left_alone() -> None:
    intent_id = uuid4()
    gateway = FakeDiddiPay(intent_id)
    repo = FakePaymentRepo()
    await _pending_topup(repo, gateway)
    repo.topups[list(repo.topups)[0]].status = TopupStatus.SUCCEEDED

    report = await _service(repo, gateway).reconcile_pending(min_age_seconds=0)

    assert report.checked == 0
    assert gateway.reads == []
