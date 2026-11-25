"""Ticket 040, Rewards contract 061: honoured quote, offer block, offers and referral relays."""

from __future__ import annotations

import json
from decimal import Decimal
from uuid import UUID, uuid4

import httpx
import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application import rewards_offers as offers_module
from app_base.modules.ride.application import services as ride_services
from app_base.modules.ride.application.rewards_offers import RewardsOffersService
from app_base.modules.ride.application.services import _ride_detail_payload
from app_base.modules.ride.infra.diddirewards_client import DiddiRewardsClient
from app_base.shared_kernel.types import GeoPoint
from tests.test_ride_quote_service import service_with_repositories

pytestmark = pytest.mark.unit

OFFER_ID = "22222222-2222-2222-2222-222222222222"


def _offer(**extra) -> dict:
    return {
        "offer_id": OFFER_ID,
        "name": "Bienvenue",
        "description": "20 % sur tes 3 premieres courses",
        "value_type": "percent",
        "rate_percent": 20,
        "cap_per_order_minor": None,
        "uses_total": 3,
        "uses_used": 1,
        "uses_left": 2,
        "use_number": 2,
        "progress": None,
        "ends_at": None,
        "services": ["go"],
        "state": "usable",
        "reason": None,
        "history": [{"service_operation_id": "ride-1", "discount_amount_minor": 246, "state": "used", "at": "x"}],
        **extra,
    }


class HonouringRewards:
    """Rewards of contract 061: quote gives quote_id + offer; reserve honours or refuses."""

    def __init__(self, *, reserve_error: ApiError | None = None, reserved: int | None = None,
                 honoured: bool = True) -> None:
        self.quote_id = str(uuid4())
        self.reserve_error = reserve_error
        self.reserved = reserved
        self.honoured = honoured
        self.quote_calls: list[dict] = []
        self.reserve_calls: list[dict] = []
        self.released: list[dict] = []

    async def quote(self, **kwargs) -> dict:
        self.quote_calls.append(kwargs)
        fare = kwargs["amount_initial_minor"]
        return {
            "eligible": True, "entitlement_id": str(uuid4()), "campaign_version_id": str(uuid4()),
            "campaign_id": OFFER_ID, "discount_amount_minor": 246, "final_amount_minor": fare - 246,
            "currency": "XOF", "reason": None, "quote_id": self.quote_id,
            "honoured_until": kwargs.get("honour_until"), "offer": _offer(),
        }

    async def reserve(self, **kwargs) -> dict:
        self.reserve_calls.append(kwargs)
        if self.reserve_error is not None:
            raise self.reserve_error
        amount = self.reserved if self.reserved is not None else kwargs["requested_amount_minor"]
        return {
            "reservation_id": str(uuid4()), "reserved_amount_minor": amount, "status": "pending",
            "duplicate": False, "quote_honoured": self.honoured,
            "quote_reason": None if self.honoured else "right_partly_used",
        }

    async def release(self, **kwargs) -> dict:
        self.released.append(kwargs)
        return {}


async def _quote_and_order(rewards, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ride_services.settings, "diddi_rewards_enabled", True)
    monkeypatch.setattr(ride_services.settings, "diddi_rewards_auto_quote_enabled", True)
    service, quotes, rides = service_with_repositories()
    service.diddirewards = rewards
    passenger_id = uuid4()
    estimate = await service.create_quote(
        passenger_user_id=passenger_id,
        pickup=GeoPoint(lat=5.35, lng=-4.01),
        pickup_address="Cocody",
        dropoff=GeoPoint(lat=5.32, lng=-4.02),
        dropoff_address="Plateau",
        vehicle_category="standard",
        comfort_level="standard",
    )
    quote = next(iter(quotes.quotes.values()))
    return service, estimate, quote, passenger_id, rides


@pytest.mark.asyncio
async def test_estimate_asks_rewards_to_honour_until_quote_expiry_and_relays_the_offer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rewards = HonouringRewards()
    _, estimate, quote, _, _ = await _quote_and_order(rewards, monkeypatch)

    assert rewards.quote_calls[0]["honour_until"] == estimate["expires_at"]
    assert str(quote.rewards_quote_id) == rewards.quote_id
    assert estimate["rewards"]["offer"]["offer_id"] == OFFER_ID
    assert estimate["rewards"]["offer"]["use_number"] == 2
    assert estimate["rewards"]["discount_amount_minor"] == 246


@pytest.mark.asyncio
async def test_order_sends_quote_id_and_keeps_the_quoted_discount(monkeypatch: pytest.MonkeyPatch) -> None:
    rewards = HonouringRewards()
    service, _, quote, passenger_id, _ = await _quote_and_order(rewards, monkeypatch)

    ride = await service.request_ride(
        passenger_user_id=passenger_id, quote_id=quote.id, payment_method="cash", scheduled_at=None
    )

    assert str(rewards.reserve_calls[0]["quote_id"]) == rewards.quote_id
    assert ride.rewards_discount_amount == Decimal("246")
    assert ride.rewards_status == "reserved"
    # Offer frozen on the ride, without the customer's history of other orders.
    assert ride.rewards_offer["offer_id"] == OFFER_ID
    assert "history" not in ride.rewards_offer


@pytest.mark.asyncio
async def test_right_used_up_refuses_the_order_with_a_stable_code(monkeypatch: pytest.MonkeyPatch) -> None:
    refusal = ApiError(
        409, "REWARDS_OPERATION_FAILED", "DiddiRewards a refuse l'operation.",
        {"detail": {"code": "right_used_up", "message": "used by another order"}},
    )
    rewards = HonouringRewards(reserve_error=refusal)
    service, _, quote, passenger_id, _ = await _quote_and_order(rewards, monkeypatch)

    with pytest.raises(ApiError) as excinfo:
        await service.request_ride(
            passenger_user_id=passenger_id, quote_id=quote.id, payment_method="cash", scheduled_at=None
        )

    assert excinfo.value.status_code == 409
    assert excinfo.value.code == "REWARDS_OFFER_ALREADY_USED"


@pytest.mark.asyncio
async def test_other_rewards_refusals_are_not_renamed(monkeypatch: pytest.MonkeyPatch) -> None:
    refusal = ApiError(409, "REWARDS_OPERATION_FAILED", "x", {"detail": {"code": "quote_already_used"}})
    service, _, quote, passenger_id, _ = await _quote_and_order(HonouringRewards(reserve_error=refusal), monkeypatch)

    with pytest.raises(ApiError) as excinfo:
        await service.request_ride(
            passenger_user_id=passenger_id, quote_id=quote.id, payment_method="cash", scheduled_at=None
        )

    assert excinfo.value.code == "REWARDS_OPERATION_FAILED"


@pytest.mark.asyncio
async def test_right_partly_used_still_lowers_to_what_rewards_reserved(monkeypatch: pytest.MonkeyPatch) -> None:
    rewards = HonouringRewards(reserved=100, honoured=False)
    service, _, quote, passenger_id, _ = await _quote_and_order(rewards, monkeypatch)

    ride = await service.request_ride(
        passenger_user_id=passenger_id, quote_id=quote.id, payment_method="cash", scheduled_at=None
    )

    assert ride.rewards_discount_amount == Decimal("100")


@pytest.mark.asyncio
async def test_ride_detail_shows_the_offer_to_the_passenger_not_the_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    rewards = HonouringRewards()
    service, _, quote, passenger_id, _ = await _quote_and_order(rewards, monkeypatch)
    ride = await service.request_ride(
        passenger_user_id=passenger_id, quote_id=quote.id, payment_method="cash", scheduled_at=None
    )

    assert _ride_detail_payload(ride, None, viewer_role="passenger")["rewards"]["offer"]["name"] == "Bienvenue"
    assert _ride_detail_payload(ride, None, viewer_role="driver")["rewards"]["offer"] is None


# --- client -----------------------------------------------------------------------------------


def _client(handler) -> DiddiRewardsClient:
    return DiddiRewardsClient(
        base_url="http://rewards.test", service_token="tok", transport=httpx.MockTransport(handler)
    )


@pytest.mark.asyncio
async def test_client_sends_honour_until_and_quote_id() -> None:
    bodies: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={"reservation_id": str(uuid4())})

    client = _client(handler)
    await client.quote(
        consumer_id=uuid4(), campaign_id=None, amount_initial_minor=1000, request_id="r",
        honour_until="2026-11-25T18:00:00Z",
    )
    quote_id = uuid4()
    await client.reserve(
        consumer_id=uuid4(), entitlement_id=uuid4(), ride_id=uuid4(), requested_amount_minor=246,
        idempotency_key="k", request_id="r", quote_id=quote_id,
    )

    assert bodies[0]["honour_until"] == "2026-11-25T18:00:00Z"
    assert bodies[1]["quote_id"] == str(quote_id)


@pytest.mark.asyncio
async def test_client_offer_and_referral_routes() -> None:
    seen: list[httpx.Request] = []
    consumer = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={})

    client = _client(handler)
    await client.consumer_offers(consumer_id=consumer, request_id="r1")
    await client.my_referral_code(consumer_id=consumer, request_id="r2")
    await client.apply_referral_code(consumer_id=consumer, code="AB12CD34", idempotency_key="key-1", request_id="r3")

    base = f"/internal/v1/rewards/integrations/diddigo/consumers/{consumer}"
    assert [(r.method, r.url.path) for r in seen] == [
        ("GET", f"{base}/offers"),
        ("GET", f"{base}/referral-code"),
        ("POST", f"{base}/referral-code/apply"),
    ]
    assert seen[0].content == b""
    assert seen[2].headers["Idempotency-Key"] == "key-1"
    assert json.loads(seen[2].content) == {"code": "AB12CD34"}


# --- app relays ---------------------------------------------------------------------------------


class FakeRewardsRelay:
    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error
        self.applied: list[dict] = []

    async def consumer_offers(self, **_) -> dict:
        if self.error:
            raise self.error
        return {"consumer_id": "x", "service_code": "go", "offers": [_offer()]}

    async def my_referral_code(self, **_) -> dict:
        return {"code": "AB12CD34", "link": None, "referred_count": 0, "pending_count": 1}

    async def apply_referral_code(self, **kwargs) -> dict:
        self.applied.append(kwargs)
        return {"status": "refused", "reason": "own_code", "offer_id": None, "duplicate": False}


@pytest.fixture
def rewards_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(offers_module.settings, "diddi_rewards_enabled", True)


@pytest.mark.asyncio
async def test_my_offers_relays_the_list(rewards_on) -> None:
    result = await RewardsOffersService(FakeRewardsRelay()).list_offers(uuid4(), request_id="r")
    assert result == {"offers": [_offer()]}


@pytest.mark.asyncio
async def test_one_offer_or_404(rewards_on) -> None:
    service = RewardsOffersService(FakeRewardsRelay())
    assert (await service.get_offer(uuid4(), UUID(OFFER_ID), request_id="r"))["name"] == "Bienvenue"
    with pytest.raises(ApiError) as excinfo:
        await service.get_offer(uuid4(), uuid4(), request_id="r")
    assert excinfo.value.status_code == 404 and excinfo.value.code == "REWARDS_OFFER_NOT_FOUND"


@pytest.mark.asyncio
async def test_referral_code_scopes_idempotency_key_per_customer(rewards_on) -> None:
    relay = FakeRewardsRelay()
    user = uuid4()
    result = await RewardsOffersService(relay).apply_referral_code(
        user, code=" ab12cd34 ", idempotency_key="app-key-1", request_id="r"
    )
    assert result == {"status": "refused", "reason": "own_code", "offer_id": None, "duplicate": False}
    assert relay.applied[0]["idempotency_key"] == f"diddigo:user:{user}:referral-code:app-key-1"
    assert relay.applied[0]["code"] == "ab12cd34"


@pytest.mark.asyncio
async def test_my_referral_relays_counts_only(rewards_on) -> None:
    result = await RewardsOffersService(FakeRewardsRelay()).my_referral(uuid4(), request_id="r")
    assert result["code"] == "AB12CD34" and result["link"] is None and result["pending_count"] == 1


@pytest.mark.asyncio
async def test_rewards_failure_or_switched_off_is_503(rewards_on, monkeypatch: pytest.MonkeyPatch) -> None:
    down = RewardsOffersService(FakeRewardsRelay(error=ApiError(403, "REWARDS_OPERATION_FAILED", "scope")))
    with pytest.raises(ApiError) as excinfo:
        await down.list_offers(uuid4(), request_id="r")
    assert excinfo.value.status_code == 503 and excinfo.value.code == "REWARDS_UNAVAILABLE"

    monkeypatch.setattr(offers_module.settings, "diddi_rewards_enabled", False)
    with pytest.raises(ApiError) as excinfo:
        await RewardsOffersService(FakeRewardsRelay()).list_offers(uuid4(), request_id="r")
    assert excinfo.value.code == "REWARDS_UNAVAILABLE"
