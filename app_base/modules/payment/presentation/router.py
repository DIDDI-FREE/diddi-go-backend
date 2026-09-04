"""Payment router — `/v1/payments/*` endpoints per API contract §3.

`/payments/{ride_id}/confirm-cash` is driver-only — gated via
`require_role("driver")` from the auth dep module.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.auth_deps import get_current_user, require_business_driver, require_role
from app_base.core.deps import driver_wallet_service, payment_service, session_dep
from app_base.core.errors import ApiError
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.payment.application.services import PaymentService
from app_base.modules.payment.application.wallet_service import DriverWalletService
from app_base.modules.payment.presentation.schemas import (
    CashConfirmationRequest,
    DriverTopupRequest,
    PaymentPreparationRequest,
)
from app_base.modules.ride.domain.entities import DriverProfile

router = APIRouter(prefix="/payments", tags=["payment"])
wallet_router = APIRouter(prefix="/drivers/me/wallet", tags=["driver-wallet"])
admin_wallet_router = APIRouter(prefix="/admin/drivers", tags=["admin-driver-wallet"])
admin_payment_router = APIRouter(prefix="/admin/payments", tags=["admin-payment"])
internal_router = APIRouter(prefix="/internal/webhooks", tags=["internal-webhooks"])
return_router = APIRouter(tags=["payment-return"])


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


@wallet_router.get("")
async def get_my_wallet(
    service: DriverWalletService = Depends(driver_wallet_service),
    current_user: UserModel = Depends(get_current_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    return await service.get_wallet(driver_user_id=current_user.id)


@wallet_router.get("/ledger")
async def get_my_ledger(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: DriverWalletService = Depends(driver_wallet_service),
    current_user: UserModel = Depends(get_current_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    return await service.get_ledger(driver_user_id=current_user.id, page=page, page_size=page_size)


@wallet_router.post("/topups", status_code=201)
async def create_driver_topup(
    payload: DriverTopupRequest,
    service: DriverWalletService = Depends(driver_wallet_service),
    current_user: UserModel = Depends(get_current_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    return await service.create_topup(
        driver_user_id=current_user.id,
        amount=Decimal(payload.amount),
        method=payload.method,
        customer_email=payload.customer_email,
        customer_phone=payload.customer_phone or current_user.phone,
        callback_url=payload.callback_url,
    )


@wallet_router.get("/topups/{topup_id}")
async def get_driver_topup(
    topup_id: UUID,
    service: DriverWalletService = Depends(driver_wallet_service),
    current_user: UserModel = Depends(get_current_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    return await service.get_topup(driver_user_id=current_user.id, topup_id=topup_id)


@admin_wallet_router.get("/{driver_id}/wallet")
async def admin_get_driver_wallet(
    driver_id: UUID,
    service: DriverWalletService = Depends(driver_wallet_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.admin_get_wallet(driver_id)


@admin_wallet_router.get("/{driver_id}/wallet/ledger")
async def admin_get_driver_ledger(
    driver_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: DriverWalletService = Depends(driver_wallet_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.admin_get_ledger(driver_id, page=page, page_size=page_size)


@admin_payment_router.post("/reconcile")
async def reconcile_pending_payments(
    limit: int | None = Query(default=None, ge=1, le=500),
    service: PaymentService = Depends(payment_service),
    session: AsyncSession = Depends(session_dep),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    """Force a DiddiPay reconciliation sweep instead of waiting for the timer."""
    report = await service.reconcile_pending(limit=limit)
    await session.commit()
    return report.as_dict()


@admin_payment_router.post("/rides/{ride_id}/reconcile")
async def reconcile_ride_payment(
    ride_id: UUID,
    service: PaymentService = Depends(payment_service),
    session: AsyncSession = Depends(session_dep),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    report = await service.reconcile_transaction(ride_id)
    await session.commit()
    return report.as_dict()


@admin_payment_router.post("/topups/{topup_id}/reconcile")
async def reconcile_driver_topup(
    topup_id: UUID,
    service: PaymentService = Depends(payment_service),
    session: AsyncSession = Depends(session_dep),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    report = await service.reconcile_topup(topup_id)
    await session.commit()
    return report.as_dict()


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


@return_router.get("/payments/return", response_class=HTMLResponse)
@return_router.get("/wallet/return", response_class=HTMLResponse)
async def payment_browser_return(
    trxref: str | None = None,
    reference: str | None = None,
) -> str:
    """Browser landing page after provider checkout.

    This is deliberately not a payment confirmation endpoint. Paystack/DiddiPay
    may redirect a browser here before the signed server callback is processed,
    so the application must still poll DiddiGo for the authoritative status.
    """
    escaped_reference = (reference or trxref or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>DiddiGo - Paiement</title>
    <style>
      body {{ font-family: sans-serif; margin: 0; padding: 32px; background: #f8fafc; color: #0f172a; }}
      main {{
        max-width: 520px; margin: 10vh auto; background: white;
        border-radius: 20px; padding: 28px;
        box-shadow: 0 24px 70px rgba(15, 23, 42, 0.12);
      }}
      h1 {{ margin-top: 0; font-size: 24px; }}
      p {{ line-height: 1.5; }}
      code {{ background: #e2e8f0; padding: 3px 6px; border-radius: 6px; }}
    </style>
  </head>
  <body>
    <main>
      <h1>Retour paiement DiddiGo</h1>
      <p>Le paiement est en cours de verification.</p>
      <p>Vous pouvez revenir dans l'application. Elle va relire DiddiGo pour confirmer le statut final.</p>
      <p>Reference: <code>{escaped_reference or "non fournie"}</code></p>
    </main>
  </body>
</html>"""
