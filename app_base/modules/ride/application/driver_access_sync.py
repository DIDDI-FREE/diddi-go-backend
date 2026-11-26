"""Tell DiddiFreeID when a DiddiGo driver is enabled, suspended or rejected (ticket 084).

Decision 2026-11-26: the service that validates a professional records it in DiddiFreeID,
which keeps the date of the first validation (bonuses "for drivers validated from date X"
read it). Every change is queued in `ride.driver_access_status_events` and sent until
DiddiFreeID accepts it; a refusal (4xx) is kept and alerted, never resent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.ride.domain.driver_access import access_status
from app_base.modules.ride.domain.entities import DriverProfile
from app_base.modules.ride.infra.driver_access_repository import SqlAlchemyDriverAccessStatusRepository
from app_base.modules.ride.infra.identity_capability_client import (
    CapabilityDeliveryError,
    IdentityCapabilityClient,
)


@dataclass
class DriverAccessStatusPublisher:
    repository: SqlAlchemyDriverAccessStatusRepository
    required_documents: set[str]

    async def publish(self, profile: DriverProfile, *, reason: str) -> str | None:
        """Queue the driver's access status if it changed. Returns the status queued, or None."""
        status = access_status(profile, required_documents=self.required_documents)
        if status is None:
            return None
        if await self.repository.last_status(profile.user_id) == status:
            return None
        await self.repository.enqueue(
            user_id=profile.user_id, access_status=status, reason=reason, source="kyc", now=datetime.now(UTC)
        )
        log_event(
            "identity.driver_access.enqueued", user_id=profile.user_id, driver_id=profile.id,
            access_status=status, reason=reason,
        )
        return status


@dataclass
class DriverAccessStatusDispatcher:
    repository: SqlAlchemyDriverAccessStatusRepository
    client: IdentityCapabilityClient
    retry_base_seconds: int = 5
    retry_max_seconds: int = 300

    async def deliver_due(self, *, batch_size: int) -> int:
        if not settings.driver_access_status_sync_enabled:
            # Statuses wait in the queue until DiddiFreeID has the route (ticket 083).
            return 0
        now = datetime.now(UTC)
        delivered = 0
        for event in await self.repository.list_due(now=now, limit=batch_size):
            if await self.repository.has_waiting_before(event):
                continue
            try:
                await self.client.send_driver_access_status(event)
            except CapabilityDeliveryError as exc:
                if exc.status_code is not None and 400 <= exc.status_code < 500 and exc.status_code not in {401, 403}:
                    await self.repository.mark_refused(event, error=f"{exc.status_code} {exc.error_code}")
                    log_event(
                        "identity.driver_access.refused", level="error", user_id=event.user_id,
                        event_id=event.event_id, access_status=event.access_status,
                        status_code=exc.status_code, error_code=exc.error_code,
                    )
                    continue
                # DiddiFreeID down, or a scope missing (fixed in configuration): try again later.
                delay = min(self.retry_base_seconds * (2 ** min(event.attempts, 8)), self.retry_max_seconds)
                await self.repository.mark_retry(
                    event, next_attempt_at=now + timedelta(seconds=delay), error=f"{exc.status_code} {exc}"
                )
                log_event(
                    "identity.driver_access.retry", level="warning", user_id=event.user_id,
                    event_id=event.event_id, attempts=event.attempts, status_code=exc.status_code,
                )
                continue
            await self.repository.mark_delivered(event, now=now)
            delivered += 1
            log_event(
                "identity.driver_access.delivered", user_id=event.user_id, event_id=event.event_id,
                access_status=event.access_status, source=event.source,
            )
        return delivered
