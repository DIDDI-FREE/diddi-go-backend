"""Incident staging 2026-11-24 : un devis avec `campaign_id` renvoyait 500.

Causes : le client demandait a DiddiFreeID le scope inexistant `diddirewards:benefits:write` (403), et l'erreur
remontait brute ; par ailleurs un consommateur non eligible (entitlement_id null) aurait provoque un 502.
Regles verifiees ici :
- le jeton S2S est demande avec les scopes reellement exiges par Rewards ;
- un refus de DiddiFreeID devient une ApiError 503 REWARDS_UNAVAILABLE lisible ;
- un devis reste servi plein tarif quand Rewards est indisponible, avec `rewards.eligible=false` ;
- un consommateur non eligible obtient un devis plein tarif sans erreur.
"""

from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application import services as ride_services
from app_base.modules.ride.application.services import _ride_detail_payload
from app_base.modules.ride.domain.entities import ComfortLevel, Ride, RideStatus, VehicleCategory
from app_base.modules.ride.infra.diddirewards_client import DiddiRewardsClient
from app_base.shared_kernel.types import GeoPoint
from tests.test_ride_quote_service import service_with_repositories

pytestmark = pytest.mark.unit

REQUIRED_SCOPES = {
    "diddirewards:benefits:quote",
    "diddirewards:benefits:reserve",
    "diddirewards:benefits:release",
    "diddirewards:benefits:consume",
    "diddirewards:benefits:correct",
    "diddirewards:reconcile",
}


def _client(handler) -> DiddiRewardsClient:
    return DiddiRewardsClient(
        base_url="http://rewards.test",
        client_id="diddigo-staging-rewards",
        service_token=None,
        client_secret="secret",
        identity_base_url="http://identity.test",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_service_token_requests_every_scope_rewards_routes_require() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/identity/v1/auth/service/token":
            seen["scope"] = dict(httpx.QueryParams(request.content.decode()))["scope"]
            seen["audience"] = dict(httpx.QueryParams(request.content.decode()))["audience"]
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 600})
        return httpx.Response(
            200,
            json={
                "eligible": True,
                "entitlement_id": str(uuid4()),
                "discount_amount_minor": 100,
                "final_amount_minor": 900,
            },
        )

    await _client(handler).quote(
        consumer_id=uuid4(), campaign_id=str(uuid4()), amount_initial_minor=1000, request_id="r1"
    )
    assert set(seen["scope"].split()) == REQUIRED_SCOPES
    assert seen["audience"] == "diddirewards"
    assert "diddirewards:benefits:write" not in seen["scope"]


@pytest.mark.asyncio
async def test_identity_refusal_becomes_explicit_503() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403, json={"error": {"code": "INVALID_SCOPE", "message": "Scope non autorisé pour ce client."}}
        )

    with pytest.raises(ApiError) as excinfo:
        await _client(handler).quote(
            consumer_id=uuid4(), campaign_id=str(uuid4()), amount_initial_minor=1000, request_id="r1"
        )
    assert excinfo.value.status_code == 503
    assert excinfo.value.code == "REWARDS_UNAVAILABLE"
    assert excinfo.value.details["identity_status"] == 403
    assert excinfo.value.details["identity_error"]["error"]["code"] == "INVALID_SCOPE"


@pytest.mark.asyncio
async def test_startup_scope_check_resolves_the_configured_s2s_token() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(httpx.QueryParams(request.content.decode())))
        return httpx.Response(200, json={"access_token": "tok", "expires_in": 600})

    await _client(handler).validate_service_access()

    assert seen["audience"] == "diddirewards"
    assert set(seen["scope"].split()) == REQUIRED_SCOPES


class RewardsDown:
    async def quote(self, **_: object) -> dict:
        raise ApiError(
            503, "REWARDS_UNAVAILABLE", "DiddiFreeID a refuse le jeton DiddiRewards.", {"identity_status": 403}
        )


class RewardsIneligible:
    async def quote(self, **_: object) -> dict:
        return {
            "eligible": False,
            "entitlement_id": None,
            "campaign_version_id": None,
            "discount_amount_minor": 0,
            "final_amount_minor": 0,
            "currency": "XOF",
            "reason": "No eligible entitlement",
        }


class RewardsEligible:
    entitlement_id = str(uuid4())
    version_id = str(uuid4())

    async def quote(self, *, amount_initial_minor: int, **_: object) -> dict:
        discount = amount_initial_minor * 20 // 100
        return {
            "eligible": True,
            "entitlement_id": self.entitlement_id,
            "campaign_version_id": self.version_id,
            "discount_amount_minor": discount,
            "final_amount_minor": amount_initial_minor - discount,
            "currency": "XOF",
            "reason": None,
        }


async def _quote_with(rewards, monkeypatch: pytest.MonkeyPatch) -> tuple[dict, object]:
    monkeypatch.setattr(ride_services.settings, "diddi_rewards_enabled", True)
    service, quotes, _ = service_with_repositories()
    service.diddirewards = rewards
    result = await service.create_quote(
        passenger_user_id=uuid4(),
        pickup=GeoPoint(lat=5.35, lng=-4.01),
        pickup_address="Cocody",
        dropoff=GeoPoint(lat=5.32, lng=-4.02),
        dropoff_address="Plateau",
        vehicle_category="standard",
        comfort_level="standard",
        campaign_id="11111111-1111-1111-1111-111111111111",
    )
    return result, next(iter(quotes.quotes.values()))


@pytest.mark.asyncio
async def test_quote_survives_rewards_outage_at_full_price(monkeypatch: pytest.MonkeyPatch) -> None:
    result, quote = await _quote_with(RewardsDown(), monkeypatch)
    assert result["estimated_fare"] > 0
    assert result["rewards"]["eligible"] is False
    assert result["rewards"]["entitlement_id"] is None
    assert result["rewards"]["reason"] == "rewards_unavailable"
    assert result["rewards"]["final_amount_minor"] == result["estimated_fare"]
    assert quote.rewards_entitlement_id is None


@pytest.mark.asyncio
async def test_ineligible_consumer_gets_full_price_without_error(monkeypatch: pytest.MonkeyPatch) -> None:
    result, quote = await _quote_with(RewardsIneligible(), monkeypatch)
    assert result["rewards"]["eligible"] is False
    assert result["rewards"]["reason"] == "No eligible entitlement"
    assert result["rewards"]["discount_amount_minor"] == 0
    assert result["rewards"]["final_amount_minor"] == result["estimated_fare"]
    assert quote.rewards_entitlement_id is None and quote.rewards_discount_amount == Decimal("0")


@pytest.mark.asyncio
async def test_eligible_consumer_sees_discount(monkeypatch: pytest.MonkeyPatch) -> None:
    rewards = RewardsEligible()
    result, quote = await _quote_with(rewards, monkeypatch)
    fare = result["estimated_fare"]
    assert result["rewards"]["eligible"] is True
    assert result["rewards"]["entitlement_id"] == rewards.entitlement_id
    assert result["rewards"]["discount_amount_minor"] == fare * 20 // 100
    assert result["rewards"]["final_amount_minor"] == fare - fare * 20 // 100
    assert str(quote.rewards_entitlement_id) == rewards.entitlement_id


@pytest.mark.parametrize("viewer_role", ["passenger", "driver"])
def test_ride_detail_exposes_gross_discount_and_payable_amount(viewer_role: str) -> None:
    ride = Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        status=RideStatus.IN_PROGRESS,
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.STANDARD,
        estimated_fare=Decimal("1234"),
        final_fare=Decimal("1234"),
        rewards_campaign_id="campaign-1",
        rewards_discount_amount=Decimal("246"),
        rewards_status="reserved",
    )

    payload = _ride_detail_payload(ride, None, viewer_role=viewer_role)

    assert payload["final_fare"] == 1234
    assert payload["rewards"] == {
        "campaign_id": "campaign-1",
        "discount_amount_minor": 246,
        "client_payable_amount": 988,
        "status": "reserved",
        "offer": None,
    }


class RewardsReserving(RewardsEligible):
    """Rewards that reserves at most `available` (ticket 003: a short reservation is a normal case)."""

    def __init__(self, available: int | None) -> None:
        self.available = available
        self.released: list[dict] = []

    async def reserve(self, *, requested_amount_minor: int, **_: object) -> dict:
        body: dict = {"reservation_id": str(uuid4()), "status": "pending", "duplicate": False}
        if self.available is not None:
            body["reserved_amount_minor"] = min(requested_amount_minor, self.available)
        return body

    async def release(self, **kwargs: object) -> dict:
        self.released.append(kwargs)
        return {}


async def _ride_with(rewards, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ride_services.settings, "diddi_rewards_enabled", True)
    service, quotes, _ = service_with_repositories()
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
    ride = await service.request_ride(
        passenger_user_id=passenger_id, quote_id=quote.id, payment_method="cash", scheduled_at=None
    )
    return ride, quote


@pytest.mark.asyncio
async def test_full_reservation_keeps_quoted_discount(monkeypatch: pytest.MonkeyPatch) -> None:
    ride, quote = await _ride_with(RewardsReserving(available=10_000), monkeypatch)
    assert quote.rewards_discount_amount > 0
    assert ride.rewards_discount_amount == quote.rewards_discount_amount
    assert ride.rewards_status == "reserved"


@pytest.mark.asyncio
async def test_partial_reservation_lowers_ride_discount_to_reserved_amount(monkeypatch: pytest.MonkeyPatch) -> None:
    rewards = RewardsReserving(available=32)
    ride, quote = await _ride_with(rewards, monkeypatch)
    assert quote.rewards_discount_amount > 32
    assert ride.rewards_discount_amount == Decimal("32")
    assert ride.rewards_status == "reserved"
    assert rewards.released == []
    payload = _ride_detail_payload(ride, None, viewer_role="passenger")
    assert payload["rewards"]["discount_amount_minor"] == 32
    assert payload["rewards"]["client_payable_amount"] == int(ride.estimated_fare) - 32


@pytest.mark.asyncio
async def test_empty_reservation_drops_discount_and_releases(monkeypatch: pytest.MonkeyPatch) -> None:
    rewards = RewardsReserving(available=0)
    ride, _ = await _ride_with(rewards, monkeypatch)
    assert ride.rewards_discount_amount == Decimal("0")
    assert ride.rewards_status == "released"
    assert len(rewards.released) == 1
    payload = _ride_detail_payload(ride, None, viewer_role="passenger")
    assert payload["rewards"]["client_payable_amount"] == int(ride.estimated_fare)


@pytest.mark.asyncio
async def test_reservation_without_amount_keeps_quoted_discount(monkeypatch: pytest.MonkeyPatch) -> None:
    ride, quote = await _ride_with(RewardsReserving(available=None), monkeypatch)
    assert ride.rewards_discount_amount == quote.rewards_discount_amount
    assert ride.rewards_status == "reserved"


class RewardsPickingBestOffer:
    """Rewards asked without campaign_id (ticket 040): it picks the customer's best offer itself."""

    campaign_id = "22222222-2222-2222-2222-222222222222"

    def __init__(self, *, eligible: bool = True, error: ApiError | None = None) -> None:
        self.eligible = eligible
        self.error = error
        self.calls: list[dict] = []

    async def quote(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        fare = kwargs["amount_initial_minor"]
        if not self.eligible:
            return {
                "eligible": False, "entitlement_id": None, "campaign_version_id": None,
                "discount_amount_minor": 0, "final_amount_minor": fare, "reason": "No eligible entitlement",
            }
        return {
            "eligible": True, "entitlement_id": str(uuid4()), "campaign_version_id": str(uuid4()),
            "campaign_id": self.campaign_id, "discount_amount_minor": 100, "final_amount_minor": fare - 100,
            "reason": None,
        }


async def _auto_quote(rewards, monkeypatch: pytest.MonkeyPatch, *, auto: bool = True) -> tuple[dict, object]:
    monkeypatch.setattr(ride_services.settings, "diddi_rewards_enabled", True)
    monkeypatch.setattr(ride_services.settings, "diddi_rewards_auto_quote_enabled", auto)
    service, quotes, _ = service_with_repositories()
    service.diddirewards = rewards
    result = await service.create_quote(
        passenger_user_id=uuid4(),
        pickup=GeoPoint(lat=5.35, lng=-4.01),
        pickup_address="Cocody",
        dropoff=GeoPoint(lat=5.32, lng=-4.02),
        dropoff_address="Plateau",
        vehicle_category="standard",
        comfort_level="standard",
    )
    return result, next(iter(quotes.quotes.values()))


@pytest.mark.asyncio
async def test_auto_quote_applies_the_best_offer_without_campaign_id(monkeypatch: pytest.MonkeyPatch) -> None:
    rewards = RewardsPickingBestOffer()
    result, quote = await _auto_quote(rewards, monkeypatch)

    assert len(rewards.calls) == 1 and rewards.calls[0]["campaign_id"] is None
    assert result["rewards"]["eligible"] is True
    assert result["rewards"]["campaign_id"] == rewards.campaign_id
    assert result["rewards"]["discount_amount_minor"] == 100
    assert result["rewards"]["final_amount_minor"] == result["estimated_fare"] - 100
    assert quote.rewards_campaign_id == rewards.campaign_id


@pytest.mark.asyncio
async def test_auto_quote_with_no_offer_is_a_plain_full_price_estimate(monkeypatch: pytest.MonkeyPatch) -> None:
    result, quote = await _auto_quote(RewardsPickingBestOffer(eligible=False), monkeypatch)

    assert "rewards" not in result
    assert quote.rewards_entitlement_id is None and quote.rewards_reason is None


@pytest.mark.asyncio
async def test_auto_quote_survives_rewards_outage_without_a_rewards_block(monkeypatch: pytest.MonkeyPatch) -> None:
    rewards = RewardsPickingBestOffer(error=ApiError(422, "REWARDS_OPERATION_FAILED", "campaign_id required"))
    result, quote = await _auto_quote(rewards, monkeypatch)

    assert result["estimated_fare"] > 0
    assert "rewards" not in result
    assert quote.rewards_reason is None


@pytest.mark.asyncio
async def test_auto_quote_off_never_calls_rewards_without_campaign_id(monkeypatch: pytest.MonkeyPatch) -> None:
    rewards = RewardsPickingBestOffer()
    result, _ = await _auto_quote(rewards, monkeypatch, auto=False)

    assert rewards.calls == []
    assert "rewards" not in result


@pytest.mark.asyncio
async def test_client_quote_omits_campaign_id_when_none() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.content
        return httpx.Response(200, json={"eligible": False, "discount_amount_minor": 0, "final_amount_minor": 1000})

    client = DiddiRewardsClient(
        base_url="http://rewards.test", service_token="tok", transport=httpx.MockTransport(handler)
    )
    await client.quote(consumer_id=uuid4(), campaign_id=None, amount_initial_minor=1000, request_id="r1")

    assert b"campaign_id" not in seen["body"]
    assert b'"service_code":"go"' in seen["body"]
