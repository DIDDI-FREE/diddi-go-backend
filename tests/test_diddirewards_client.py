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
