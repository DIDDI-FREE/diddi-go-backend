"""Idempotency store for Backoffice KYC decisions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError


@dataclass(frozen=True)
class KycCommandReservation:
    redis_key: str
    fingerprint: str
    cached_response: dict[str, Any] | None = None


class KycCommandStore:
    def __init__(self, redis: Redis, *, ttl_seconds: int = 86400) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def reserve(self, *, client_id: str, idempotency_key: str, payload: dict[str, Any]) -> KycCommandReservation:
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
        ).hexdigest()
        redis_key = f"diddigo:kyc-command:{client_id}:{idempotency_key}"
        pending = json.dumps({"fingerprint": fingerprint, "state": "pending"})
        if await self._redis.set(redis_key, pending, ex=self._ttl_seconds, nx=True):
            return KycCommandReservation(redis_key, fingerprint)

        existing_raw = await self._redis.get(redis_key)
        if existing_raw is None:
            return await self.reserve(client_id=client_id, idempotency_key=idempotency_key, payload=payload)
        existing = json.loads(existing_raw)
        if existing.get("fingerprint") != fingerprint:
            raise ApiError(409, ErrorCode.IDEMPOTENCY_CONFLICT, "Cette cle d'idempotence designe une autre commande.")
        if existing.get("state") == "done" and isinstance(existing.get("response"), dict):
            return KycCommandReservation(redis_key, fingerprint, existing["response"])
        raise ApiError(409, ErrorCode.IDEMPOTENCY_IN_PROGRESS, "Cette commande KYC est deja en cours.")

    async def complete(self, reservation: KycCommandReservation, response: dict[str, Any]) -> None:
        value = json.dumps(
            {"fingerprint": reservation.fingerprint, "state": "done", "response": response},
            separators=(",", ":"),
        )
        await self._redis.set(reservation.redis_key, value, ex=self._ttl_seconds)

    async def release(self, reservation: KycCommandReservation) -> None:
        await self._redis.delete(reservation.redis_key)
