from __future__ import annotations

import json
from uuid import uuid4

import httpx
import pytest

from app_base.core.errors import ApiError
from app_base.modules.payment.infra.diddipay_client import DiddiPayClient

pytestmark = pytest.mark.unit


def _s2s_client(handler) -> DiddiPayClient:
    return DiddiPayClient(
        base_url="https://pay.test",
        identity_base_url="https://identity.test",
        client_id="diddigo-staging",
        service_key=None,
        client_secret="secret",
        transport=httpx.MockTransport(handler),
    )


def _legacy_client(handler) -> DiddiPayClient:
    return DiddiPayClient(
        base_url="https://pay.test",
        identity_base_url=None,
        client_id="diddigo",
        service_key="legacy-key",
        client_secret=None,
        transport=httpx.MockTransport(handler),
    )


async def test_create_payment_intent_uses_s2s_token_with_write_scope() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/service/token"):
            assert request.headers["X-Client-ID"] == "diddigo-staging"
            body = request.content.decode()
            assert "audience=diddipay" in body
            assert "scope=diddipay%3Apayment-intents%3Awrite" in body
            return httpx.Response(200, json={"access_token": "s2s-token", "expires_in": 600})
        assert request.url.path == "/payment-intents"
        assert request.headers["Authorization"] == "Bearer s2s-token"
        assert request.headers["X-Client-ID"] == "diddigo-staging"
        assert "X-Service-Key" not in request.headers
        assert request.headers["Idempotency-Key"] == "idem-1"
        return httpx.Response(201, json={"id": "intent-1", "status": "requires_action"})

    result = await _s2s_client(handler).create_payment_intent({"amount": 5000}, idempotency_key="idem-1")
    assert result["id"] == "intent-1"


async def test_get_payment_intent_uses_read_scope_and_caches_token() -> None:
    token_requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_requests
        if request.url.path.endswith("/auth/service/token"):
            token_requests += 1
            body = request.content.decode()
            assert "scope=diddipay%3Apayment-intents%3Aread" in body
            return httpx.Response(200, json={"access_token": "s2s-token", "expires_in": 600})
        return httpx.Response(200, json={"id": "intent-1", "status": "succeeded"})

    client = _s2s_client(handler)
    intent_id = uuid4()
    await client.get_payment_intent(intent_id)
    await client.get_payment_intent(intent_id)
    assert token_requests == 1


async def test_falls_back_to_legacy_service_key_when_no_client_secret() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert not request.url.path.endswith("/auth/service/token")
        assert request.headers["X-Client-ID"] == "diddigo"
        assert request.headers["X-Service-Key"] == "legacy-key"
        assert "Authorization" not in request.headers
        return httpx.Response(200, json={"id": "intent-1", "status": "succeeded"})

    result = await _legacy_client(handler).get_payment_intent(uuid4())
    assert result["id"] == "intent-1"


async def test_get_payment_intent_returns_none_on_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/service/token"):
            return httpx.Response(200, json={"access_token": "s2s-token", "expires_in": 600})
        return httpx.Response(404)

    assert await _s2s_client(handler).get_payment_intent(uuid4()) is None


async def test_create_payment_intent_raises_api_error_on_rejection() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/service/token"):
            return httpx.Response(200, json={"access_token": "s2s-token", "expires_in": 600})
        return httpx.Response(
            409, json={"error": {"code": "IDEMPOTENCY_CONFLICT", "message": "conflict"}}
        )

    with pytest.raises(ApiError) as exc_info:
        await _s2s_client(handler).create_payment_intent({"amount": 5000}, idempotency_key="idem-1")
    assert exc_info.value.status_code == 409


async def test_not_configured_without_any_credentials() -> None:
    def unreached(request: httpx.Request) -> httpx.Response:
        raise AssertionError("must not call DiddiPay without configured credentials")

    client = DiddiPayClient(
        base_url="https://pay.test",
        identity_base_url=None,
        client_id="diddigo",
        service_key=None,
        client_secret=None,
        transport=httpx.MockTransport(unreached),
    )
    with pytest.raises(ApiError) as exc_info:
        await client.get_payment_intent(uuid4())
    assert exc_info.value.status_code == 503
