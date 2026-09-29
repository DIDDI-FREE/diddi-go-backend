"""Driver priority engine — application services (SCRUM-63 Phase 3).

Two thin services around the single ledger:

  * ``PriorityLedger`` (write) — the ONLY writer. The ride lifecycle calls
    ``record_ride_outcome`` at exactly the terminal transitions; admins call
    ``record_boost``. All point amounts come from ``PriorityPolicy``.
  * ``DriverPriorityService`` (read) — the matcher-facing provider. One batched
    windowed query; exposes the point→seconds bonus via the same policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app_base.modules.ride.domain.entities import Ride, RideStatus
from app_base.modules.ride.domain.interfaces import PriorityLedgerPort
from app_base.modules.ride.domain.priority import (
    DEFAULT_ZONE_ID,
    DispatchConfig,
    PriorityEvent,
    PriorityEventKind,
    PriorityPolicy,
    PriorityScore,
)

_OUTCOME_KINDS: dict[RideStatus, PriorityEventKind] = {
    RideStatus.COMPLETED: PriorityEventKind.RIDE_COMPLETED,
    RideStatus.CANCELLED_BY_DRIVER: PriorityEventKind.RIDE_CANCELLED_BY_DRIVER,
}


@dataclass
class PriorityLedger:
    """The single writer. Delegates every point amount to the policy so no
    arithmetic lives in the ride lifecycle."""

    repo: PriorityLedgerPort
    config: DispatchConfig

    async def record_ride_outcome(self, ride: Ride) -> None:
        """Record a completed / driver-cancelled ride as a priority fact.

        No-op for any other status or an unassigned ride — so the lifecycle
        call sites stay one-liners with no branching of their own."""
        kind = _OUTCOME_KINDS.get(ride.status)
        if kind is None or ride.driver_id is None:
            return
        policy = PriorityPolicy(self.config)
        await self.repo.append(
            PriorityEvent(
                driver_id=ride.driver_id,
                kind=kind,
                points=policy.points_for_ride_outcome(kind),
                zone_id=DEFAULT_ZONE_ID,
                ride_id=ride.id,
                reason=kind.value,
            ),
        )

    async def record_boost(
        self,
        driver_id: UUID,
        *,
        points: int,
        expires_at: datetime,
        reason: str,
        zone_id: UUID | None = None,
    ) -> None:
        """Grant an explicit, expiring priority boost (UC-106)."""
        await self.repo.append(
            PriorityEvent(
                driver_id=driver_id,
                kind=PriorityEventKind.TEMP_BOOST,
                points=points,
                zone_id=zone_id,
                reason=reason,
                expires_at=expires_at,
            ),
        )


@dataclass
class DriverPriorityService:
    """The single reader (matcher-facing ``PriorityProvider``)."""

    repo: PriorityLedgerPort
    config: DispatchConfig

    async def scores_for(
        self, driver_ids: list[UUID], *, zone_id: UUID = DEFAULT_ZONE_ID, at: datetime | None = None,
    ) -> dict[UUID, PriorityScore]:
        if not driver_ids:
            return {}
        now = at or datetime.now(UTC)
        since = now - timedelta(days=self.config.priority_window_days)
        totals = await self.repo.windowed_points(driver_ids, since=since, zone_id=zone_id, now=now)
        return {driver_id: PriorityScore(driver_id, points) for driver_id, points in totals.items()}

    def bonus_seconds(self, points: int) -> int:
        return PriorityPolicy(self.config).bonus_seconds(points)
