"""Ticket 014: every Rewards reservation ends by exactly one of confirm or release.

Staging 2026-11-24, ride 502bb120: reserve OK, confirm refused (409), then nothing. The reservation
stayed pending and blocked the passenger's entitlement. Rules checked here:
- a confirm Rewards refuses for good is ended by a release (`confirmation_refused`);
- a confirm that fails for a passing reason stays open and the sweep retries it;
- a release that failed is retried with the same reason as the first attempt;
- reserve no longer sends the quote expiry as `expires_at`.
"""

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.payment.application.rewards_reservations import close_reservation
from app_base.modules.payment.application.services import PaymentService
from app_base.modules.payment.domain.entities import PaymentStatus
from app_base.modules.ride.application import services as ride_services
from app_base.modules.ride.application.rewards_release import release_reason
from app_base.modules.ride.domain.entities import Ride, RideStatus
from app_base.shared_kernel.types import GeoPoint
from tests.test_ride_quote_service import service_with_repositories

pytestmark = pytest.mark.unit


def refused(status_code: int = 409) -> ApiError:
    return ApiError(status_code, "REWARDS_OPERATION_FAILED", "DiddiRewards a refuse l'operation.")


def down() -> ApiError:
    return ApiError(503, "REWARDS_UNAVAILABLE", "DiddiRewards est indisponible.")


class FakeRewards:
    def __init__(self, *, confirm_error: Exception | None = None, release_error: Exception | None = None) -> None:
        self.confirm_error = confirm_error
        self.release_error = release_error
        self.confirms: list[dict] = []
        self.releases: list[dict] = []
        self.consumption_id = uuid4()

    async def confirm(self, **kwargs) -> dict:
        self.confirms.append(kwargs)
        if self.confirm_error is not None:
            raise self.confirm_error
        return {"consumption_id": str(self.consumption_id)}

    async def release(self, **kwargs) -> dict:
        self.releases.append(kwargs)
        if self.release_error is not None:
            raise self.release_error
        return {}


class FakeRideRepo:
    def __init__(self) -> None:
        self.saved = 0

    async def save(self, ride):
        self.saved += 1
        return ride


class FakePaymentRepo:
    def __init__(self, payment) -> None:
        self.payment = payment

    async def find_by_ride_id(self, ride_id):
        return self.payment


def reserved_ride(status: RideStatus = RideStatus.COMPLETED, **overrides) -> Ride:
    fields = {
        "id": uuid4(),
        "passenger_user_id": uuid4(),
        "status": status,
        "pickup_location": GeoPoint(lat=5.35, lng=-4.01),
        "dropoff_location": GeoPoint(lat=5.36, lng=-4.02),
        "estimated_fare": Decimal("1234"),
        "final_fare": Decimal("1234"),
        "driver_payout_estimate": Decimal("1012"),
        "rewards_reservation_id": uuid4(),
        "rewards_discount_amount": Decimal("246"),
        "rewards_status": "reserved",
    }
    fields.update(overrides)
    return Ride(**fields)


def collected_payment(ride: Ride, status: PaymentStatus = PaymentStatus.COLLECTED):
    return SimpleNamespace(
        id=uuid4(), ride_id=ride.id, status=status, amount=Decimal("988"), payment_intent_id=None,
        business_reference=None,
    )


def payment_service(rewards: FakeRewards, payment=None) -> PaymentService:
    return PaymentService(payment_repo=FakePaymentRepo(payment), ride_repo=FakeRideRepo(), diddirewards=rewards)


@pytest.mark.asyncio
async def test_refused_confirm_is_ended_by_a_release() -> None:
    rewards = FakeRewards(confirm_error=refused(409))
    ride = reserved_ride()
    await payment_service(rewards)._confirm_rewards_if_needed(ride, collected_payment(ride))

    assert len(rewards.releases) == 1
    release = rewards.releases[0]
    assert release["reservation_id"] == ride.rewards_reservation_id
    assert release["reason"] == "confirmation_refused"
    assert release["idempotency_key"] == f"diddigo:ride:{ride.id}:rewards-release:v1"
    assert ride.rewards_status == "confirmation_refused"
    assert ride.rewards_consumption_id is None


@pytest.mark.asyncio
async def test_refused_confirm_is_not_sent_again() -> None:
    rewards = FakeRewards(confirm_error=refused(409))
    ride = reserved_ride()
    service = payment_service(rewards)
    await service._confirm_rewards_if_needed(ride, collected_payment(ride))
    await service._confirm_rewards_if_needed(ride, collected_payment(ride))

    assert len(rewards.confirms) == 1
    assert len(rewards.releases) == 1


@pytest.mark.parametrize("error", [down(), refused(401), RuntimeError("boom")])
@pytest.mark.asyncio
async def test_passing_confirm_failure_keeps_the_reservation_open(error: Exception) -> None:
    rewards = FakeRewards(confirm_error=error)
    ride = reserved_ride()
    await payment_service(rewards)._confirm_rewards_if_needed(ride, collected_payment(ride))

    assert rewards.releases == []
    assert ride.rewards_status == "reserved"


@pytest.mark.asyncio
async def test_refused_confirm_with_failed_release_is_retried_by_the_sweep() -> None:
    rewards = FakeRewards(confirm_error=refused(409), release_error=down())
    ride = reserved_ride()
    payment = collected_payment(ride)
    service = payment_service(rewards, payment)
    await service._confirm_rewards_if_needed(ride, payment)
    assert ride.rewards_status == "release_deferred"

    rewards.release_error = None
    outcome = await close_reservation(
        ride, diddirewards=rewards, ride_repo=service.ride_repo, payment_repo=service.payment_repo, payments=service
    )

    assert outcome == "released"
    assert ride.rewards_status == "confirmation_refused"
    assert len(rewards.confirms) == 1
    assert [call["reason"] for call in rewards.releases] == ["confirmation_refused", "confirmation_refused"]


@pytest.mark.asyncio
async def test_sweep_retries_a_deferred_confirm() -> None:
    rewards = FakeRewards()
    ride = reserved_ride()
    payment = collected_payment(ride)
    service = payment_service(rewards, payment)

    outcome = await close_reservation(
        ride, diddirewards=rewards, ride_repo=service.ride_repo, payment_repo=service.payment_repo, payments=service
    )

    assert outcome == "confirmed"
    assert ride.rewards_status == "confirmed"
    assert ride.rewards_consumption_id == rewards.consumption_id
    assert rewards.releases == []


@pytest.mark.asyncio
async def test_sweep_leaves_an_unpaid_completed_ride_alone() -> None:
    rewards = FakeRewards()
    ride = reserved_ride()
    payment = collected_payment(ride, PaymentStatus.REQUIRES_ACTION)
    service = payment_service(rewards, payment)

    outcome = await close_reservation(
        ride, diddirewards=rewards, ride_repo=service.ride_repo, payment_repo=service.payment_repo, payments=service
    )

    assert outcome is None
    assert rewards.confirms == [] and rewards.releases == []
    assert ride.rewards_status == "reserved"


@pytest.mark.asyncio
async def test_sweep_retries_a_deferred_release_with_the_cancel_reason() -> None:
    rewards = FakeRewards()
    ride = reserved_ride(
        RideStatus.CANCELLED_BY_PASSENGER, rewards_status="release_deferred", cancellation_reason="changed_mind"
    )
    service = payment_service(rewards)

    outcome = await close_reservation(
        ride, diddirewards=rewards, ride_repo=service.ride_repo, payment_repo=service.payment_repo, payments=service
    )

    assert outcome == "released"
    assert ride.rewards_status == "released"
    assert rewards.releases[0]["reason"] == "changed_mind"


@pytest.mark.asyncio
async def test_sweep_releases_an_abandoned_ride_still_reserved() -> None:
    rewards = FakeRewards()
    ride = reserved_ride(RideStatus.NO_DRIVER_FOUND)
    service = payment_service(rewards)

    outcome = await close_reservation(
        ride, diddirewards=rewards, ride_repo=service.ride_repo, payment_repo=service.payment_repo, payments=service
    )

    assert outcome == "released"
    assert rewards.releases[0]["reason"] == "no_driver_found"


@pytest.mark.asyncio
async def test_release_refused_for_good_stops_the_retries() -> None:
    rewards = FakeRewards(release_error=refused(409))
    ride = reserved_ride(RideStatus.NO_DRIVER_FOUND, rewards_status="release_deferred")
    service = payment_service(rewards)

    outcome = await close_reservation(
        ride, diddirewards=rewards, ride_repo=service.ride_repo, payment_repo=service.payment_repo, payments=service
    )

    assert outcome is None
    assert ride.rewards_status == "release_refused"


def test_release_reason_is_derived_from_the_ride() -> None:
    assert release_reason(reserved_ride(RideStatus.IN_PROGRESS)) is None
    assert release_reason(reserved_ride(RideStatus.IN_PROGRESS, rewards_discount_amount=Decimal("0"))) == (
        "nothing_reserved"
    )
    assert release_reason(reserved_ride(RideStatus.NO_DRIVER_FOUND)) == "no_driver_found"
    assert release_reason(reserved_ride(RideStatus.CANCELLED_BY_DRIVER, cancellation_reason="driver_unavailable")) == (
        "driver_unavailable"
    )
    assert release_reason(reserved_ride(RideStatus.CANCELLED_BY_PASSENGER)) == "cancelled"
    assert release_reason(reserved_ride(RideStatus.COMPLETED)) == "confirmation_refused"


class RewardsRecordingReserve:
    def __init__(self) -> None:
        self.reserve_calls: list[dict] = []
        self.entitlement_id = str(uuid4())

    async def quote(self, *, amount_initial_minor: int, **_: object) -> dict:
        return {
            "eligible": True,
            "entitlement_id": self.entitlement_id,
            "campaign_version_id": str(uuid4()),
            "discount_amount_minor": 100,
            "final_amount_minor": amount_initial_minor - 100,
        }

    async def reserve(self, **kwargs) -> dict:
        self.reserve_calls.append(kwargs)
        return {"reservation_id": str(uuid4()), "reserved_amount_minor": kwargs["requested_amount_minor"]}


@pytest.mark.asyncio
async def test_reserve_does_not_send_the_quote_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ride_services.settings, "diddi_rewards_enabled", True)
    service, quotes, _ = service_with_repositories()
    rewards = RewardsRecordingReserve()
    service.diddirewards = rewards
    passenger_id = uuid4()
    await service.create_quote(
        passenger_user_id=passenger_id,
        pickup=GeoPoint(lat=5.35, lng=-4.01),
        pickup_address="Cocody",
        dropoff=GeoPoint(lat=5.32, lng=-4.02),
        dropoff_address="Plateau",
        vehicle_category="standard",
        comfort_level="standard",
        campaign_id="11111111-1111-1111-1111-111111111111",
    )
    quote = next(iter(quotes.quotes.values()))
    await service.request_ride(
        passenger_user_id=passenger_id, quote_id=quote.id, payment_method="cash", scheduled_at=None
    )

    assert len(rewards.reserve_calls) == 1
    assert "expires_at" not in rewards.reserve_calls[0]
