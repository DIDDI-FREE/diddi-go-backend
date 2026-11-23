from uuid import UUID

import httpx
import pytest

from app_base.modules.ride.infra.diddirewards_client import DiddiRewardsClient


@pytest.mark.unit
@pytest.mark.asyncio
async def test_quote_uses_explicit_diddigo_contract_and_headers() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["request"] = request
        seen["json"] = request.content
        return httpx.Response(
            200,
            json={
                "eligible": True,
                "entitlement_id": "11111111-1111-1111-1111-111111111111",
                "campaign_version_id": "22222222-2222-2222-2222-222222222222",
                "discount_amount_minor": 1000,
                "final_amount_minor": 4000,
                "currency": "XOF",
                "reason": "eligible",
            },
        )

    client = DiddiRewardsClient(
        base_url="http://rewards.test",
        client_id="diddigo-staging",
        service_token="secret-token",
        transport=httpx.MockTransport(handler),
    )
    result = await client.quote(
        consumer_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        campaign_id="campaign-1",
        amount_initial_minor=5000,
        request_id="request-1",
    )

    assert result["eligible"] is True
    assert str(seen["request"].url) == "http://rewards.test/internal/v1/rewards/integrations/diddigo/benefits/quote"
    assert seen["request"].headers["Authorization"] == "Bearer secret-token"
    assert seen["request"].headers["X-Client-ID"] == "diddigo-staging"
    assert seen["request"].headers["X-Request-ID"] == "request-1"
    assert b'"service_code":"go"' in seen["json"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reserve_sends_idempotency_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/benefits/reserve")
        assert request.headers["Idempotency-Key"] == "diddigo:ride:reserve:1"
        return httpx.Response(200, json={"reservation_id": "33333333-3333-3333-3333-333333333333"})

    client = DiddiRewardsClient(
        base_url="http://rewards.test",
        service_token="secret-token",
        transport=httpx.MockTransport(handler),
    )
    result = await client.reserve(
        consumer_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        entitlement_id=UUID("11111111-1111-1111-1111-111111111111"),
        ride_id=UUID("44444444-4444-4444-4444-444444444444"),
        requested_amount_minor=1000,
        idempotency_key="diddigo:ride:reserve:1",
        request_id="request-2",
    )

    assert result["reservation_id"] == "33333333-3333-3333-3333-333333333333"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_confirm_correct_and_reconciliation_use_contract_routes() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        assert request.headers["Idempotency-Key"].startswith("diddigo:")
        if request.url.path.endswith("/confirm"):
            return httpx.Response(200, json={"consumption_id": "55555555-5555-5555-5555-555555555555"})
        if request.url.path.endswith("/correct"):
            return httpx.Response(200, json={"correction_id": "66666666-6666-6666-6666-666666666666"})
        return httpx.Response(200, json={"status": "matched"})

    client = DiddiRewardsClient(
        base_url="http://rewards.test",
        service_token="secret-token",
        transport=httpx.MockTransport(handler),
    )
    ride_id = UUID("44444444-4444-4444-4444-444444444444")
    consumption_id = UUID("55555555-5555-5555-5555-555555555555")
    assert (await client.confirm(
        reservation_id=UUID("33333333-3333-3333-3333-333333333333"),
        ride_id=ride_id,
        applied_discount_minor=1000,
        client_paid_minor=4000,
        driver_payout_minor=3500,
        diddi_contribution_minor=1000,
        payment_reference="pay-1",
        idempotency_key="diddigo:confirm:1",
        request_id="r-1",
    ))["consumption_id"] == str(consumption_id)
    assert (await client.correct(
        consumption_id=consumption_id,
        amount_minor=1000,
        reason="refunded",
        payment_reference="pay-1",
        idempotency_key="diddigo:correct:1",
        request_id="r-2",
    ))["correction_id"]
    assert (await client.reconciliation(
        consumption_id=consumption_id,
        confirmed_discount_minor=1000,
        external_reference=str(ride_id),
        details={"status": "succeeded"},
        idempotency_key="diddigo:reconciliation:1",
        request_id="r-3",
    ))["status"] == "matched"
    assert paths == [
        "/internal/v1/rewards/integrations/diddigo/benefits/confirm",
        "/internal/v1/rewards/integrations/diddigo/benefits/correct",
        "/internal/v1/rewards/integrations/diddigo/reconciliation",
    ]
