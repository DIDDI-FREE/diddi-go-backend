"""Offers and referral codes of the signed-in customer (ticket 040).

Names accepted by the PM (ticket 073): `GET /v1/me/offers`, `GET /v1/me/offers/{offer_id}`,
`POST /v1/me/referral/code`, `GET /v1/me/referral`. Pure relays to DiddiRewards.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

from app_base.core.auth_deps import get_current_active_user
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.application.rewards_offers import RewardsOffersService

router = APIRouter(prefix="/me", tags=["me-offers"])


class ReferralCodeApplyRequest(BaseModel):
    code: str = Field(min_length=1, max_length=80)


def rewards_offers_service(request: Request) -> RewardsOffersService:
    return RewardsOffersService(diddirewards=getattr(request.app.state, "diddirewards", None))


def _request_id(value: str | None) -> str:
    return value or str(uuid4())


@router.get("/offers")
async def list_my_offers(
    service: RewardsOffersService = Depends(rewards_offers_service),
    current_user: UserModel = Depends(get_current_active_user),
    request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict:
    """Every offer of the customer valid on rides, all states, history included, newest first."""
    return await service.list_offers(current_user.id, request_id=_request_id(request_id))


@router.get("/offers/{offer_id}")
async def get_my_offer(
    offer_id: UUID,
    service: RewardsOffersService = Depends(rewards_offers_service),
    current_user: UserModel = Depends(get_current_active_user),
    request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict:
    """One offer of the list. 404 `REWARDS_OFFER_NOT_FOUND` if the customer has no such offer."""
    return await service.get_offer(current_user.id, offer_id, request_id=_request_id(request_id))


@router.post("/referral/code")
async def apply_referral_code(
    payload: ReferralCodeApplyRequest,
    service: RewardsOffersService = Depends(rewards_offers_service),
    current_user: UserModel = Depends(get_current_active_user),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=100),
    request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict:
    """A code typed by the customer. 200 with `accepted`, or `refused` and a reason of the fixed list.

    On 503 `REWARDS_UNAVAILABLE`, send the same request again with the same `Idempotency-Key`.
    """
    return await service.apply_referral_code(
        current_user.id,
        code=payload.code,
        idempotency_key=idempotency_key,
        request_id=_request_id(request_id),
    )


@router.get("/referral")
async def get_my_referral(
    service: RewardsOffersService = Depends(rewards_offers_service),
    current_user: UserModel = Depends(get_current_active_user),
    request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> dict:
    """My referral code, the link to share (null for now), the limits and the friends count."""
    return await service.my_referral(current_user.id, request_id=_request_id(request_id))
