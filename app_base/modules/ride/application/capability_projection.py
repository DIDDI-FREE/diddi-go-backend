"""Durable publishing and reconciliation of the DiddiGo driver projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app_base.core.metrics import increment
from app_base.core.observability import current_request_id, log_event
from app_base.modules.ride.domain.capability_projection import DriverProjectionCandidate
from app_base.modules.ride.domain.capability_projection_interfaces import (
    DriverCapabilityProjectionRepository,
)
from app_base.modules.ride.infra.identity_capability_client import (
    CapabilityDeliveryError,
    IdentityCapabilityClient,
)
from app_base.shared_kernel.contracts.capabilities import CapabilityStatusPublisher


@dataclass
class DurableDriverCapabilityPublisher(CapabilityStatusPublisher):
    repository: DriverCapabilityProjectionRepository

    async def publish_driver_status(
        self, user_id: UUID, *, operational_status: str, actions: list[str],
    ) -> bool:
        event = await self.repository.enqueue(
            user_id,
            operational_status=operational_status,
            actions=actions,
            request_id=current_request_id(),
        )
        if event is None:
            log_event(
                "identity.capability.projection.unchanged",
                user_id=user_id,
                operational_status=operational_status,
            )
            return True
        increment("diddigo_capability_projection_events_total", {"result": "enqueued"})
        log_event(
            "identity.capability.projection.enqueued",
            user_id=user_id,
            event_id=event.event_id,
            projection_version=event.projection_version,
            operational_status=operational_status,
        )
        return True


@dataclass
class DriverCapabilityProjectionDispatcher:
    repository: DriverCapabilityProjectionRepository
    client: IdentityCapabilityClient
    retry_base_seconds: int = 5
    retry_max_seconds: int = 300

    async def deliver_due(self, *, batch_size: int) -> int:
        now = datetime.now(UTC)
        events = await self.repository.list_due(now=now, limit=batch_size)
        for event in events:
            try:
                await self.client.send_driver_status(event)
            except CapabilityDeliveryError as exc:
                if exc.conflict:
                    await self.repository.mark_conflict(event, now=now, error=str(exc))
                    result = "conflict"
                elif exc.status_code == 404:
                    # The user does not exist in DiddiFreeID: retrying cannot
                    # succeed, so park the event instead of retrying forever.
                    await self.repository.mark_dead_letter(event, now=now, error=str(exc))
                    result = "dead_letter"
                else:
                    delay = min(self.retry_base_seconds * (2 ** min(event.attempts, 8)), self.retry_max_seconds)
                    await self.repository.mark_retry(
                        event,
                        now=now,
                        next_attempt_at=now + timedelta(seconds=delay),
                        error=str(exc),
                    )
                    result = "retry"
                increment("diddigo_capability_projection_events_total", {"result": result})
                log_event(
                    "identity.capability.projection.delivery_failed",
                    level="warning" if result == "retry" else "error",
                    user_id=event.user_id,
                    event_id=event.event_id,
                    projection_version=event.projection_version,
                    attempt=event.attempts + 1,
                    result=result,
                    status_code=exc.status_code,
                    error_code=exc.error_code,
                )
                continue
            await self.repository.mark_succeeded(event, now=now)
            increment("diddigo_capability_projection_events_total", {"result": "succeeded"})
            log_event(
                "identity.capability.projection.delivered",
                user_id=event.user_id,
                event_id=event.event_id,
                projection_version=event.projection_version,
                attempt=event.attempts + 1,
                operational_status=event.operational_status,
            )
        return len(events)

    async def reconcile(
        self,
        *,
        candidates: list[DriverProjectionCandidate],
        online_user_ids: set[UUID],
        refresh_before: datetime,
        batch_size: int,
    ) -> dict[str, int]:
        enqueued = 0
        for candidate in candidates:
            status, actions = _candidate_status(candidate)
            if status == "offline" and candidate.user_id in online_user_ids:
                status, actions = "online", ["go_offline"]
            event = await self.repository.enqueue(
                candidate.user_id,
                operational_status=status,
                actions=actions,
                request_id="capability-reconciliation",
            )
            if event is not None:
                enqueued += 1
        refreshed = await self.repository.schedule_stale_refresh(
            before=refresh_before,
            now=datetime.now(UTC),
            limit=batch_size,
        )
        if enqueued or refreshed:
            increment("diddigo_capability_projection_reconciliations_total", {"result": "changed"})
            log_event(
                "identity.capability.projection.reconciled",
                enqueued=enqueued,
                refreshed=refreshed,
            )
        return {"enqueued": enqueued, "refreshed": refreshed}


def _candidate_status(candidate: DriverProjectionCandidate) -> tuple[str, list[str]]:
    if candidate.profile_status == "pending_verification":
        return "pending_verification", ["await_kyc_review"]
    if candidate.profile_status == "suspended":
        return "kyc_rejected", ["resubmit_kyc"]
    if candidate.vehicle_status is None:
        return "vehicle_missing", ["add_vehicle"]
    if candidate.vehicle_status == "pending_verification":
        return "vehicle_pending_verification", ["await_vehicle_review"]
    if candidate.vehicle_status == "rejected":
        return "vehicle_rejected", ["resubmit_vehicle"]
    if candidate.vehicle_status != "active" or not candidate.vehicle_active:
        return "vehicle_unavailable", ["contact_support"]
    return "offline", ["go_online"]
