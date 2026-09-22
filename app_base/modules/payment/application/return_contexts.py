"""Short-lived, one-time browser return contexts stored in Redis."""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

from redis.asyncio import Redis


@dataclass(frozen=True)
class PaymentReturnContext:
    flow: str
    surface: str
    user_id: UUID
    resource_id: UUID
    payment_intent_id: UUID


class PaymentReturnContextStore:
    def __init__(self, redis: Redis, *, ttl_seconds: int = 900) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def create(self, *, flow: str, surface: str, user_id: UUID, resource_id: UUID) -> str:
        token = secrets.token_urlsafe(32)
        payload = {
            "flow": flow,
            "surface": surface,
            "user_id": str(user_id),
            "resource_id": str(resource_id),
            "payment_intent_id": None,
        }
        await self._redis.set(self._key(token), json.dumps(payload), ex=self._ttl_seconds)
        return token

    async def bind_payment_intent(self, token: str, payment_intent_id: UUID) -> None:
        key = self._key(token)
        raw = await self._redis.get(key)
        if raw is None:
            return
        payload = json.loads(raw)
        payload["payment_intent_id"] = str(payment_intent_id)
        ttl = await self._redis.ttl(key)
        if ttl > 0:
            await self._redis.set(key, json.dumps(payload), ex=ttl)

    async def consume(self, token: str, *, expected_surface: str) -> PaymentReturnContext | None:
        raw = await self._redis.getdel(self._key(token))
        if raw is None:
            return None
        try:
            payload = json.loads(raw)
            if payload["surface"] != expected_surface or not payload["payment_intent_id"]:
                return None
            return PaymentReturnContext(
                flow=payload["flow"],
                surface=payload["surface"],
                user_id=UUID(payload["user_id"]),
                resource_id=UUID(payload["resource_id"]),
                payment_intent_id=UUID(payload["payment_intent_id"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    @staticmethod
    def callback_url(base_url: str | None, token: str) -> str | None:
        if not base_url:
            return None
        parts = urlsplit(base_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query["context"] = token
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    @staticmethod
    def _key(token: str) -> str:
        return f"diddigo:payment-return:{token}"
