"""Payment router — `/v1/payments/*` endpoints per API contract §3.

`/payments/{ride_id}/confirm-cash` is driver-only — gated via
`require_role("driver")` from the auth dep module.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, Response

from app_base.core.auth_deps import get_current_user, require_business_driver
from app_base.core.deps import payment_service
from app_base.core.errors import ApiError
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.payment.application.services import PaymentService
from app_base.modules.payment.presentation.schemas import CashConfirmationRequest, PaymentPreparationRequest
from app_base.modules.ride.domain.entities import DriverProfile

router = APIRouter(prefix="/payments", tags=["payment"])
internal_router = APIRouter(prefix="/internal/webhooks", tags=["internal-webhooks"])


@router.post("/{ride_id}/prepare")
async def prepare_payment(
    ride_id: UUID,
    payload: PaymentPreparationRequest,
    service: PaymentService = Depends(payment_service),
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    return await service.prepare_payment(
        ride_id,
        payload.method,
        payer_user_id=current_user.id,
        customer_email=payload.customer_email,
        customer_phone=payload.customer_phone or current_user.phone,
        callback_url=payload.callback_url,
    )


@router.post("/{ride_id}/confirm-cash")
async def confirm_cash(
    ride_id: UUID,
    payload: CashConfirmationRequest,
    service: PaymentService = Depends(payment_service),
    current_user: UserModel = Depends(get_current_user),
    driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    if driver_profile is None:
        raise ApiError(403, "DRIVER_PROFILE_REQUIRED", "Un profil chauffeur est requis pour encaisser.")
    return await service.confirm_cash(
        ride_id,
        Decimal(payload.amount_collected),
        collected_by=driver_profile.id,
    )


@router.get("/{ride_id}")
async def get_payment(
    ride_id: UUID,
    service: PaymentService = Depends(payment_service),
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    return await service.get_payment(ride_id)


@internal_router.post("/diddipay", status_code=204)
async def diddipay_webhook(
    request: Request,
    response: Response,
    service: PaymentService = Depends(payment_service),
    event_id: str | None = Header(default=None, alias="X-DiddiPay-Event-ID"),
    signature: str | None = Header(default=None, alias="X-DiddiPay-Signature"),
) -> Response:
    result = await service.apply_diddipay_webhook(
        raw_body=await request.body(),
        event_id_header=event_id,
        signature=signature,
    )
    if result["status"] == "duplicate":
        response.status_code = 200
    return response
