"""Scoped service-to-service KYC API consumed by the Backoffice backend."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request

from app_base.core.auth_deps import require_identity_service_token, require_s2s_admin_actor
from app_base.core.deps import driver_service, kyc_command_store
from app_base.core.observability import log_event
from app_base.core.s2s_command_store import S2SCommandStore
from app_base.core.service_scopes import DIDDIGO_AUDIENCE, KYC_DECIDE, KYC_READ
from app_base.modules.auth.domain.entities import User
from app_base.modules.ride.application.driver_service import DriverService
from app_base.modules.ride.presentation.driver_schemas import DriverKycReviewRequest

router = APIRouter(prefix="/internal/v1/drivers", tags=["internal-driver-kyc"])
require_kyc_read = require_identity_service_token(audience=DIDDIGO_AUDIENCE, required_scope=KYC_READ)
require_kyc_decide = require_identity_service_token(audience=DIDDIGO_AUDIENCE, required_scope=KYC_DECIDE)


@router.get("/kyc")
async def list_driver_kyc_queue(
    status: str = Query(default="pending_verification"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _claims: dict = Depends(require_kyc_read),
    service: DriverService = Depends(driver_service),
) -> dict:
    return await service.list_kyc_queue(status=status, page=page, page_size=page_size)


@router.get("/{driver_id}/kyc")
async def get_driver_kyc_detail(
    driver_id: UUID,
    _claims: dict = Depends(require_kyc_read),
    service: DriverService = Depends(driver_service),
) -> dict:
    return await service.get_kyc_detail(driver_id)


async def _decide(
    *,
    decision: str,
    driver_id: UUID,
    notes: str | None,
    request: Request,
    idempotency_key: str,
    claims: dict,
    actor: User,
    service: DriverService,
    commands: S2SCommandStore,
) -> dict:
    client_id = request.headers["X-Client-ID"]
    reservation = await commands.reserve(
        client_id=client_id,
        idempotency_key=idempotency_key,
        payload={"decision": decision, "driver_id": str(driver_id), "actor_user_id": str(actor.id), "notes": notes},
    )
    if reservation.cached_response is not None:
        return reservation.cached_response
    try:
        operation = service.approve_kyc if decision == "approve" else service.reject_kyc
        result = await operation(driver_id, reviewed_by_user_id=actor.id, notes=notes)
        await commands.complete(reservation, result)
    except Exception:
        await commands.release(reservation)
        raise
    log_event(
        "driver.kyc.s2s_decision",
        decision=decision,
        driver_id=driver_id,
        actor_user_id=actor.id,
        service_subject=claims.get("sub"),
        client_id=client_id,
        idempotency_key=idempotency_key,
    )
    return result


@router.post("/{driver_id}/kyc/approve")
async def approve_driver_kyc(
    driver_id: UUID,
    payload: DriverKycReviewRequest,
    request: Request,
    _request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_kyc_decide),
    actor: User = Depends(require_s2s_admin_actor),
    service: DriverService = Depends(driver_service),
    commands: S2SCommandStore = Depends(kyc_command_store),
) -> dict:
    return await _decide(
        decision="approve", driver_id=driver_id, notes=payload.notes, request=request,
        idempotency_key=idempotency_key, claims=claims, actor=actor, service=service, commands=commands,
    )


@router.post("/{driver_id}/kyc/reject")
async def reject_driver_kyc(
    driver_id: UUID,
    payload: DriverKycReviewRequest,
    request: Request,
    _request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_kyc_decide),
    actor: User = Depends(require_s2s_admin_actor),
    service: DriverService = Depends(driver_service),
    commands: S2SCommandStore = Depends(kyc_command_store),
) -> dict:
    return await _decide(
        decision="reject", driver_id=driver_id, notes=payload.notes, request=request,
        idempotency_key=idempotency_key, claims=claims, actor=actor, service=service, commands=commands,
    )
