"""Scoped service-to-service Partner admin API consumed by the Backoffice backend.

Mirrors the human-admin routes in ``router.py`` — which stay in place as a legacy
bridge during the migration — but authorizes via a Backoffice **service token**
(`diddigo:partners:*` scopes) plus a scoped human **actor** (`X-Backoffice-Actor`),
and makes every mutation idempotent and durably audited in the same transaction.
This is the exact pattern already used by the KYC and dispatch internal routers.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.auth_deps import require_backoffice_service_token, require_s2s_admin_actor
from app_base.core.deps import (
    backoffice_audit_repo,
    partner_command_store,
    partner_service,
    session_dep,
)
from app_base.core.observability import log_event
from app_base.core.s2s_command_store import S2SCommandStore
from app_base.core.service_scopes import PARTNERS_READ, PARTNERS_WRITE
from app_base.modules.audit.domain.entities import BackofficeAuditEvent
from app_base.modules.audit.domain.interfaces import BackofficeAuditRepository
from app_base.modules.auth.domain.entities import User
from app_base.modules.partner.application.services import PartnerService
from app_base.modules.partner.presentation.schemas import (
    PartnerCreateRequest,
    PartnerDriverAffiliateRequest,
    PartnerKycReviewRequest,
    PartnerKycSubmitRequest,
    PartnerMemberCreateRequest,
    PartnerUpdateRequest,
    PartnerVehicleAssignRequest,
    PartnerVehicleCreateRequest,
)

router = APIRouter(prefix="/internal/v1/admin/partners", tags=["internal-admin-partners"])

require_partners_read = require_backoffice_service_token(required_scope=PARTNERS_READ)
require_partners_write = require_backoffice_service_token(required_scope=PARTNERS_WRITE)


async def _write(
    *,
    action: str,
    run: Callable[[], Awaitable[dict]],
    request: Request,
    request_id: UUID,
    idempotency_key: str,
    claims: dict,
    actor: User,
    commands: S2SCommandStore,
    audit: BackofficeAuditRepository,
    session: AsyncSession,
    target_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> dict:
    """Run one partner mutation idempotently, audited in the same transaction.

    `target_id` is the partner the command acts on; for creation it is resolved
    from the result (`id`) once the partner exists.
    """
    client_id = request.headers["X-Client-ID"]
    reservation = await commands.reserve(
        client_id=client_id,
        idempotency_key=idempotency_key,
        payload={"action": action, "actor_user_id": str(actor.id), **(payload or {})},
    )
    if reservation.cached_response is not None:
        return reservation.cached_response
    try:
        result = await run()
        resolved_target = target_id
        if resolved_target is None:
            raw = result.get("id") if isinstance(result, dict) else None
            resolved_target = UUID(str(raw)) if raw else actor.id
        audit_event = await audit.record(
            BackofficeAuditEvent(
                client_id=client_id,
                service_subject=str(claims.get("sub") or ""),
                actor_user_id=actor.id,
                action=action,
                target_type="partner",
                target_id=resolved_target,
                request_id=request_id,
                idempotency_key=idempotency_key,
                reason="backoffice_partner_command",
                context={"result_status": result.get("status") if isinstance(result, dict) else None},
            ),
        )
        await session.commit()
        await commands.complete(reservation, result)
    except Exception:
        await commands.release(reservation)
        raise
    log_event(
        "partner.s2s_command",
        action=action,
        target_id=str(resolved_target),
        actor_user_id=actor.id,
        service_subject=claims.get("sub"),
        client_id=client_id,
        idempotency_key=idempotency_key,
        audit_id=audit_event.id,
    )
    return result


# --- reads (scope only) -----------------------------------------------------

@router.get("")
async def list_partners(
    status: str | None = None,
    partner_type: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _claims: dict = Depends(require_partners_read),
    service: PartnerService = Depends(partner_service),
) -> dict:
    return await service.list_partners(status=status, partner_type=partner_type, page=page, page_size=page_size)


@router.get("/{partner_id}")
async def get_partner(
    partner_id: UUID,
    _claims: dict = Depends(require_partners_read),
    service: PartnerService = Depends(partner_service),
) -> dict:
    return await service.get_partner(partner_id)


@router.get("/{partner_id}/members")
async def list_members(
    partner_id: UUID,
    _claims: dict = Depends(require_partners_read),
    service: PartnerService = Depends(partner_service),
) -> dict:
    return await service.list_members(partner_id)


@router.get("/{partner_id}/drivers")
async def list_drivers(
    partner_id: UUID,
    _claims: dict = Depends(require_partners_read),
    service: PartnerService = Depends(partner_service),
) -> dict:
    return await service.list_drivers(partner_id)


# --- writes (scope + actor + idempotency + audit) ---------------------------

@router.post("", status_code=201)
async def create_partner(
    payload: PartnerCreateRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    data = payload.model_dump()
    return await _write(
        action="partner.create", run=lambda: service.create_partner(**data),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.patch("/{partner_id}")
async def update_partner(
    partner_id: UUID,
    payload: PartnerUpdateRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    changes = payload.model_dump(exclude_unset=True)
    return await _write(
        action="partner.update", target_id=partner_id,
        run=lambda: service.update_partner(partner_id, **changes),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/activate")
async def activate_partner(
    partner_id: UUID,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.activate", target_id=partner_id,
        run=lambda: service.activate_partner(partner_id),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.patch("/{partner_id}/kyc")
async def submit_partner_kyc(
    partner_id: UUID,
    payload: PartnerKycSubmitRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    fields = payload.model_dump(exclude_unset=True)
    return await _write(
        action="partner.kyc.submit", target_id=partner_id,
        run=lambda: service.submit_kyc(partner_id, **fields),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/kyc/approve")
async def approve_partner_kyc(
    partner_id: UUID,
    payload: PartnerKycReviewRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.kyc.approve", target_id=partner_id,
        run=lambda: service.approve_kyc(partner_id, reviewed_by_user_id=actor.id, notes=payload.notes),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/kyc/reject")
async def reject_partner_kyc(
    partner_id: UUID,
    payload: PartnerKycReviewRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.kyc.reject", target_id=partner_id,
        run=lambda: service.reject_kyc(partner_id, reviewed_by_user_id=actor.id, notes=payload.notes),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/suspend")
async def suspend_partner(
    partner_id: UUID,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.suspend", target_id=partner_id,
        run=lambda: service.suspend_partner(partner_id),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/reject")
async def reject_partner(
    partner_id: UUID,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.reject", target_id=partner_id,
        run=lambda: service.reject_partner(partner_id),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/members", status_code=201)
async def add_member(
    partner_id: UUID,
    payload: PartnerMemberCreateRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.member.add", target_id=partner_id,
        run=lambda: service.add_member(partner_id, user_id=payload.user_id, role=payload.role),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.delete("/{partner_id}/members/{member_id}")
async def deactivate_member(
    partner_id: UUID,
    member_id: UUID,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.member.deactivate", target_id=partner_id,
        run=lambda: service.deactivate_member(partner_id, member_id),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/drivers", status_code=201)
async def affiliate_driver(
    partner_id: UUID,
    payload: PartnerDriverAffiliateRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.driver.affiliate", target_id=partner_id,
        run=lambda: service.affiliate_driver(partner_id, driver_id=payload.driver_id),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.delete("/{partner_id}/drivers/{driver_id}")
async def unaffiliate_driver(
    partner_id: UUID,
    driver_id: UUID,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.driver.unaffiliate", target_id=partner_id,
        run=lambda: service.unaffiliate_driver(partner_id, driver_id),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/vehicles", status_code=201)
async def create_partner_vehicle(
    partner_id: UUID,
    payload: PartnerVehicleCreateRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    data = payload.model_dump()
    return await _write(
        action="partner.vehicle.create", target_id=partner_id,
        run=lambda: service.create_vehicle(partner_id, **data),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/vehicles/{vehicle_id}/assign", status_code=201)
async def assign_vehicle(
    partner_id: UUID,
    vehicle_id: UUID,
    payload: PartnerVehicleAssignRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.vehicle.assign", target_id=partner_id,
        run=lambda: service.assign_vehicle(partner_id, vehicle_id=vehicle_id, driver_id=payload.driver_id),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )


@router.post("/{partner_id}/vehicles/{vehicle_id}/unassign")
async def unassign_vehicle(
    partner_id: UUID,
    vehicle_id: UUID,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_partners_write),
    actor: User = Depends(require_s2s_admin_actor),
    service: PartnerService = Depends(partner_service),
    commands: S2SCommandStore = Depends(partner_command_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> dict:
    return await _write(
        action="partner.vehicle.unassign", target_id=partner_id,
        run=lambda: service.unassign_vehicle(partner_id, vehicle_id),
        request=request, request_id=request_id, idempotency_key=idempotency_key,
        claims=claims, actor=actor, commands=commands, audit=audit, session=session,
    )
