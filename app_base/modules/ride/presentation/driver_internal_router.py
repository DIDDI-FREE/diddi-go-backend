"""Scoped S2S driver provisioning API consumed by the Backoffice backend."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.auth_deps import require_backoffice_service_token, require_s2s_admin_actor
from app_base.core.deps import (
    backoffice_audit_repo,
    driver_provisioning_command_store,
    driver_provisioning_service,
    session_dep,
)
from app_base.core.observability import log_event
from app_base.core.s2s_command_store import S2SCommandStore
from app_base.core.service_scopes import DRIVERS_WRITE
from app_base.modules.audit.domain.entities import BackofficeAuditEvent
from app_base.modules.audit.domain.interfaces import BackofficeAuditRepository
from app_base.modules.auth.domain.entities import User
from app_base.modules.ride.application.driver_provisioning_service import DriverProvisioningService
from app_base.modules.ride.presentation.driver_schemas import DriverProvisionRequest

router = APIRouter(prefix="/internal/v1/drivers", tags=["internal-drivers"])
require_drivers_write = require_backoffice_service_token(required_scope=DRIVERS_WRITE)


@router.post("/provision")
async def provision_driver_profile(
    payload: DriverProvisionRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_drivers_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: DriverProvisioningService = Depends(driver_provisioning_service),
    commands: S2SCommandStore = Depends(driver_provisioning_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    client_id = request.headers["X-Client-ID"]
    command_payload = payload.model_dump(mode="json") | {"actor_user_id": str(actor.id)}
    reservation = await commands.reserve(
        client_id=client_id,
        idempotency_key=idempotency_key,
        payload=command_payload,
    )
    if reservation.cached_response is not None:
        return reservation.cached_response

    fields = payload.model_dump(exclude={"user_id", "full_name"})
    try:
        result = await service.provision(
            user_id=payload.user_id,
            full_name=payload.full_name,
            profile_fields=fields,
        )
        audit_event = await audit.record(
            BackofficeAuditEvent(
                client_id=client_id,
                service_subject=str(claims.get("sub") or ""),
                actor_user_id=actor.id,
                action="driver.profile.provision",
                target_type="driver_identity",
                target_id=payload.user_id,
                request_id=request_id,
                idempotency_key=idempotency_key,
                reason="backoffice_driver_provisioning",
                context={
                    "created": bool(result["created"]),
                    "driver_id": result["profile"]["id"],
                },
            ),
        )
        await session.commit()
        await commands.complete(reservation, result)
    except Exception:
        await commands.release(reservation)
        raise
    log_event(
        "driver.profile.s2s_provision_command",
        target_user_id=payload.user_id,
        actor_user_id=actor.id,
        service_subject=claims.get("sub"),
        client_id=client_id,
        idempotency_key=idempotency_key,
        audit_id=audit_event.id,
        created=result["created"],
    )
    return result
