"""Scoped S2S driver provisioning API consumed by the Backoffice backend."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request

from app_base.core.auth_deps import require_identity_service_token, require_s2s_admin_actor
from app_base.core.deps import driver_provisioning_command_store, driver_provisioning_service
from app_base.core.observability import log_event
from app_base.core.s2s_command_store import S2SCommandStore
from app_base.core.service_scopes import DIDDIGO_AUDIENCE, DRIVERS_WRITE
from app_base.modules.auth.domain.entities import User
from app_base.modules.ride.application.driver_provisioning_service import DriverProvisioningService
from app_base.modules.ride.presentation.driver_schemas import DriverProvisionRequest

router = APIRouter(prefix="/internal/v1/drivers", tags=["internal-drivers"])
require_drivers_write = require_identity_service_token(
    audience=DIDDIGO_AUDIENCE,
    required_scope=DRIVERS_WRITE,
)


@router.post("/provision")
async def provision_driver_profile(
    payload: DriverProvisionRequest,
    request: Request,
    _request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_drivers_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: DriverProvisioningService = Depends(driver_provisioning_service),
    commands: S2SCommandStore = Depends(driver_provisioning_command_store),
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
    except Exception:
        await commands.release(reservation)
        raise
    await commands.complete(reservation, result)
    log_event(
        "driver.profile.s2s_provision_command",
        target_user_id=payload.user_id,
        actor_user_id=actor.id,
        service_subject=claims.get("sub"),
        client_id=client_id,
        idempotency_key=idempotency_key,
        created=result["created"],
    )
    return result
