"""App routes for offers and referral codes: pure relays to DiddiRewards (ticket 040).

DiddiGo holds no offer data. Each call asks Rewards for the signed-in customer and
passes the answer on, so "my offers" and the referral screens show what Rewards knows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.ride.infra.diddirewards_client import DiddiRewardsClient

UNAVAILABLE_MESSAGE = "Les offres sont momentanement indisponibles. Reessayez plus tard."


@dataclass
class RewardsOffersService:
    diddirewards: DiddiRewardsClient | None

    async def list_offers(self, user_id: UUID, *, request_id: str) -> dict[str, Any]:
        answer = await self._call(
            "offers.list", user_id, self._client().consumer_offers(consumer_id=user_id, request_id=request_id)
        )
        offers = answer.get("offers")
        return {"offers": offers if isinstance(offers, list) else []}

    async def get_offer(self, user_id: UUID, offer_id: UUID, *, request_id: str) -> dict[str, Any]:
        # Rewards has no single-offer route: the list is short (one customer, one service).
        for offer in (await self.list_offers(user_id, request_id=request_id))["offers"]:
            if isinstance(offer, dict) and str(offer.get("offer_id")) == str(offer_id):
                return offer
        raise ApiError(404, "REWARDS_OFFER_NOT_FOUND", "Offre introuvable.")

    async def apply_referral_code(
        self, user_id: UUID, *, code: str, idempotency_key: str, request_id: str
    ) -> dict[str, Any]:
        # Scoped per customer so two customers cannot collide on the same key at Rewards.
        key = f"diddigo:user:{user_id}:referral-code:{idempotency_key}"[:180]
        answer = await self._call(
            "referral.apply",
            user_id,
            self._client().apply_referral_code(
                consumer_id=user_id, code=code.strip(), idempotency_key=key, request_id=request_id
            ),
        )
        return {
            "status": answer.get("status"),
            "reason": answer.get("reason"),
            "offer_id": answer.get("offer_id"),
            "duplicate": bool(answer.get("duplicate", False)),
        }

    async def my_referral(self, user_id: UUID, *, request_id: str) -> dict[str, Any]:
        return await self._call(
            "referral.read", user_id, self._client().my_referral_code(consumer_id=user_id, request_id=request_id)
        )

    def _client(self) -> DiddiRewardsClient:
        if not settings.diddi_rewards_enabled or self.diddirewards is None:
            raise ApiError(503, "REWARDS_UNAVAILABLE", UNAVAILABLE_MESSAGE)
        return self.diddirewards

    async def _call(self, operation: str, user_id: UUID, call) -> dict[str, Any]:
        try:
            answer = await call
        except ApiError as exc:
            # Rewards down, scope missing (403) or any refusal: the app can only retry later.
            # The Rewards status stays in the log, not in the answer to the app.
            log_event(
                "rewards.app_relay.failed", level="error", operation=operation, user_id=user_id,
                error_code=exc.code, status_code=exc.status_code,
            )
            raise ApiError(503, "REWARDS_UNAVAILABLE", UNAVAILABLE_MESSAGE) from exc
        return answer if isinstance(answer, dict) else {}
