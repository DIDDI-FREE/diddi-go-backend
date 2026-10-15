from __future__ import annotations

import json

import httpx
import pytest

from app_base.modules.notification.infra.sms import (
    SenndoSmsProvider,
    SmsProviderError,
    YellikaSmsProvider,
    build_sms_provider,
)

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_senndo_adapter_sends_idempotent_sms() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/messages"
        assert request.headers["authorization"] == "Bearer sk_test_example"
        assert request.headers["idempotency-key"] == "sos-ride-1"
        body = json.loads(request.content)
        assert body == {
            "channel": "sms",
            "to": "+2250700000000",
            "text": "Alerte",
            "idempotencyKey": "sos-ride-1",
            "sender": "DiddiFree",
        }
        return httpx.Response(202, json={"id": "msg_1", "status": "queued"})

    provider = SenndoSmsProvider(api_key="sk_test_example", sender="DiddiFree")
    provider._client = httpx.AsyncClient(
        base_url="https://api.senndo.test",
        transport=httpx.MockTransport(handler),
    )
    delivery = await provider.send(
        recipient="+2250700000000",
        message="Alerte",
        idempotency_key="sos-ride-1",
    )
    await provider.close()

    assert delivery.provider == "senndo"
    assert delivery.status == "queued"
    assert delivery.message_id == "msg_1"


@pytest.mark.asyncio
async def test_yellika_adapter_uses_v3_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/sms/send"
        assert request.headers["authorization"] == "Bearer token"
        body = json.loads(request.content)
        assert body["recipient"] == "+2250700000000"
        assert body["sender_id"] == "DiddiFree"
        assert body["type"] == "plain"
        return httpx.Response(200, json={"data": {"uid": "sms_2", "status": "queued"}})

    provider = YellikaSmsProvider(api_token="token")
    provider._client = httpx.AsyncClient(
        base_url="https://panel.yellika.test",
        transport=httpx.MockTransport(handler),
    )
    delivery = await provider.send(
        recipient="+2250700000000",
        message="Alerte",
        idempotency_key="sos-ride-2",
    )
    await provider.close()

    assert delivery.provider == "yellika"
    assert delivery.message_id == "sms_2"


@pytest.mark.asyncio
async def test_yellika_adapter_rejects_error_inside_http_200() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "error", "message": "invalid recipient"})

    provider = YellikaSmsProvider(api_token="token")
    provider._client = httpx.AsyncClient(
        base_url="https://panel.yellika.test",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(SmsProviderError, match="provider_error"):
        await provider.send(
            recipient="invalid",
            message="Alerte",
            idempotency_key="sos-ride-3",
        )
    await provider.close()


def test_sms_provider_configuration_fails_fast() -> None:
    with pytest.raises(RuntimeError, match="SENNDO_API_KEY"):
        build_sms_provider(
            provider="senndo",
            senndo_api_key=None,
            senndo_base_url="https://api.senndo.com",
            senndo_sender=None,
            yellika_api_token=None,
            yellika_base_url="https://panel.yellikasms.com",
            yellika_sender_id="DiddiFree",
            timeout_seconds=20,
        )
