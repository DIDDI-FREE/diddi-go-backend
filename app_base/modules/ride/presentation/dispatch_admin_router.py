"""Scoped S2S dispatch administration consumed by the Backoffice (SCRUM-63).

UC-288: view/edit dispatch tunables without a redeploy. UC-110: view the active
priority rules and a driver's priority ledger. UC-106: grant an expiring
priority boost. Mutations are audited like the KYC router.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.auth_deps import require_backoffice_service_token, require_s2s_admin_actor
from app_base.core.deps import (
    backoffice_audit_repo,
    dispatch_config_store,
    priority_ledger_repo,
    session_dep,
)
from app_base.core.observability import log_event
from app_base.core.service_scopes import DISPATCH_READ, DISPATCH_WRITE
from app_base.modules.audit.domain.entities import BackofficeAuditEvent
from app_base.modules.audit.domain.interfaces import BackofficeAuditRepository
from app_base.modules.auth.domain.entities import User
from app_base.modules.ride.application.priority_service import DriverPriorityService, PriorityLedger
from app_base.modules.ride.domain.priority import DEFAULT_ZONE_ID
from app_base.modules.ride.infra.dispatch_config_store import SqlAlchemyDispatchConfigStore
from app_base.modules.ride.infra.priority_repository import SqlAlchemyPriorityLedgerRepository
from app_base.modules.ride.presentation.dispatch_schemas import (
    DispatchConfigBody,
    PriorityBoostRequest,
    PriorityEventView,
)

router = APIRouter(prefix="/internal/v1/admin/dispatch", tags=["internal-dispatch-admin"])
require_dispatch_read = require_backoffice_service_token(required_scope=DISPATCH_READ)
require_dispatch_write = require_backoffice_service_token(required_scope=DISPATCH_WRITE)

# Well-known audit target for the singleton dispatch config.
_DISPATCH_CONFIG_TARGET = UUID("00000000-0000-0000-0000-0000000000c0")


def _view(event) -> PriorityEventView:
    return PriorityEventView(
        driver_id=event.driver_id,
        kind=event.kind.value,
        points=event.points,
        zone_id=event.zone_id,
        ride_id=event.ride_id,
        reason=event.reason,
        expires_at=event.expires_at,
    )


@router.get("/config", response_model=DispatchConfigBody)
async def get_dispatch_config(
    _claims: dict = Depends(require_dispatch_read),
    store: SqlAlchemyDispatchConfigStore = Depends(dispatch_config_store),
) -> DispatchConfigBody:
    return DispatchConfigBody.from_config(await store.load())


@router.put("/config", response_model=DispatchConfigBody)
async def put_dispatch_config(
    body: DispatchConfigBody,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_dispatch_write),
    actor: User = Depends(require_s2s_admin_actor),
    store: SqlAlchemyDispatchConfigStore = Depends(dispatch_config_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> DispatchConfigBody:
    saved = await store.save(body.to_config())
    await audit.record(
        BackofficeAuditEvent(
            client_id=request.headers["X-Client-ID"],
            service_subject=str(claims.get("sub") or ""),
            actor_user_id=actor.id,
            action="dispatch.config.update",
            target_type="dispatch_config",
            target_id=_DISPATCH_CONFIG_TARGET,
            request_id=request_id,
            idempotency_key=idempotency_key,
            reason="dispatch_config_update",
            context=body.model_dump(),
        ),
    )
    await session.commit()
    log_event("dispatch.config.updated", actor_user_id=actor.id, client_id=request.headers.get("X-Client-ID"))
    return DispatchConfigBody.from_config(saved)


@router.get("/priority-rules", response_model=list[PriorityEventView])
async def list_priority_rules(
    _claims: dict = Depends(require_dispatch_read),
    ledger: SqlAlchemyPriorityLedgerRepository = Depends(priority_ledger_repo),
) -> list[PriorityEventView]:
    rules = await ledger.active_rules(now=datetime.now(UTC))
    return [_view(rule) for rule in rules]


@router.get("/drivers/{driver_id}/priority")
async def get_driver_priority(
    driver_id: UUID,
    _claims: dict = Depends(require_dispatch_read),
    ledger: SqlAlchemyPriorityLedgerRepository = Depends(priority_ledger_repo),
    store: SqlAlchemyDispatchConfigStore = Depends(dispatch_config_store),
) -> dict:
    config = await store.load()
    now = datetime.now(UTC)
    scores = await DriverPriorityService(ledger, config).scores_for([driver_id], zone_id=DEFAULT_ZONE_ID, at=now)
    events = await ledger.recent_events(driver_id)
    return {
        "driver_id": str(driver_id),
        "window_days": config.priority_window_days,
        "points": scores.get(driver_id).points if driver_id in scores else 0,
        "events": [_view(event).model_dump(mode="json") for event in events],
    }


@router.post("/priority-boosts", response_model=PriorityEventView, status_code=201)
async def grant_priority_boost(
    body: PriorityBoostRequest,
    request: Request,
    request_id: UUID = Header(alias="X-Request-ID"),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=160),
    claims: dict = Depends(require_dispatch_write),
    actor: User = Depends(require_s2s_admin_actor),
    ledger: SqlAlchemyPriorityLedgerRepository = Depends(priority_ledger_repo),
    store: SqlAlchemyDispatchConfigStore = Depends(dispatch_config_store),
    audit: BackofficeAuditRepository = Depends(backoffice_audit_repo),
    session: AsyncSession = Depends(session_dep),
) -> PriorityEventView:
    expires_at = datetime.now(UTC) + timedelta(minutes=body.duration_minutes)
    await PriorityLedger(ledger, await store.load()).record_boost(
        body.driver_id, points=body.points, expires_at=expires_at, reason=body.reason,
    )
    await audit.record(
        BackofficeAuditEvent(
            client_id=request.headers["X-Client-ID"],
            service_subject=str(claims.get("sub") or ""),
            actor_user_id=actor.id,
            action="dispatch.priority.boost",
            target_type="driver_profile",
            target_id=body.driver_id,
            request_id=request_id,
            idempotency_key=idempotency_key,
            reason=body.reason,
            context={"points": body.points, "duration_minutes": body.duration_minutes},
        ),
    )
    await session.commit()
    log_event("dispatch.priority.boosted", driver_id=body.driver_id, actor_user_id=actor.id, points=body.points)
    return PriorityEventView(
        driver_id=body.driver_id,
        kind="temp_boost",
        points=body.points,
        zone_id=None,
        ride_id=None,
        reason=body.reason,
        expires_at=expires_at,
    )
