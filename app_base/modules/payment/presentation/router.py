"""Payment router — `/v1/payments/*` endpoints per API contract §3.

`/payments/{ride_id}/confirm-cash` is driver-only — gated via
`require_role("driver")` from the auth dep module.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends

from app_base.core.auth_deps import get_current_user, require_role
from app_base.core.deps import payment_service
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.payment.application.services import PaymentService
from app_base.modules.payment.presentation.schemas import CashConfirmationRequest

router = APIRouter(prefix="/payments", tags=["payment"])


@router.post("/{ride_id}/confirm-cash")
async def confirm_cash(
    ride_id: UUID,
    payload: CashConfirmationRequest,
    service: PaymentService = Depends(payment_service),
    current_user: UserModel = Depends(require_role("driver")),
) -> dict:
    return await service.confirm_cash(
        ride_id,
        Decimal(payload.amount_collected),
        collected_by=current_user.id,
    )


@router.get("/{ride_id}")
async def get_payment(
    ride_id: UUID,
    service: PaymentService = Depends(payment_service),
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    return await service.get_payment(ride_id)
