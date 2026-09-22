from __future__ import annotations

import json
from uuid import uuid4

import pytest

from app_base.modules.payment.application.return_contexts import PaymentReturnContextStore

pytestmark = pytest.mark.unit


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def set(self, key: str, value: str, *, ex: int) -> None:
        self.values[key] = value
        self.ttls[key] = ex

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def getdel(self, key: str) -> str | None:
        self.ttls.pop(key, None)
        return self.values.pop(key, None)

    async def ttl(self, key: str) -> int:
        return self.ttls.get(key, -2)


@pytest.mark.asyncio
async def test_context_is_bound_and_consumed_once() -> None:
    redis = FakeRedis()
    store = PaymentReturnContextStore(redis, ttl_seconds=900)  # type: ignore[arg-type]
    user_id, ride_id, intent_id = uuid4(), uuid4(), uuid4()

    token = await store.create(flow="ride_payment", surface="consumer", user_id=user_id, resource_id=ride_id)
    await store.bind_payment_intent(token, intent_id)

    context = await store.consume(token, expected_surface="consumer")
    assert context is not None
    assert context.user_id == user_id
    assert context.resource_id == ride_id
    assert context.payment_intent_id == intent_id
    assert await store.consume(token, expected_surface="consumer") is None


@pytest.mark.asyncio
async def test_context_rejects_wrong_surface_tampering_and_missing_binding() -> None:
    redis = FakeRedis()
    store = PaymentReturnContextStore(redis)  # type: ignore[arg-type]
    token = await store.create(flow="driver_topup", surface="pro", user_id=uuid4(), resource_id=uuid4())

    assert await store.consume("forged-token", expected_surface="pro") is None
    assert await store.consume(token, expected_surface="consumer") is None

    unbound = await store.create(flow="ride_payment", surface="consumer", user_id=uuid4(), resource_id=uuid4())
    assert await store.consume(unbound, expected_surface="consumer") is None


def test_callback_url_preserves_provider_query_and_adds_opaque_context() -> None:
    result = PaymentReturnContextStore.callback_url("https://go.test/payments/return?source=app", "opaque")
    assert result == "https://go.test/payments/return?source=app&context=opaque"


@pytest.mark.asyncio
async def test_malformed_server_payload_is_rejected() -> None:
    redis = FakeRedis()
    store = PaymentReturnContextStore(redis)  # type: ignore[arg-type]
    await redis.set("diddigo:payment-return:bad", json.dumps({"surface": "consumer"}), ex=900)
    assert await store.consume("bad", expected_surface="consumer") is None
