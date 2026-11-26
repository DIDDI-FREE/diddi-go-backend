"""Queue of driver access statuses for DiddiFreeID (ticket 084)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.ride.infra import models as orm


class SqlAlchemyDriverAccessStatusRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def last_status(self, user_id: UUID) -> str | None:
        """Last access status queued for this driver (sent or not), to queue only changes."""
        result = await self._session.execute(
            select(orm.DriverAccessStatusEventModel.access_status)
            .where(orm.DriverAccessStatusEventModel.user_id == user_id)
            .order_by(orm.DriverAccessStatusEventModel.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def has_backfill(self, user_id: UUID) -> bool:
        result = await self._session.execute(
            select(orm.DriverAccessStatusEventModel.id)
            .where(
                orm.DriverAccessStatusEventModel.user_id == user_id,
                orm.DriverAccessStatusEventModel.source == "backfill",
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def enqueue(
        self,
        *,
        user_id: UUID,
        access_status: str,
        reason: str,
        source: str,
        now: datetime,
        enabled_at: datetime | None = None,
    ) -> orm.DriverAccessStatusEventModel:
        event = orm.DriverAccessStatusEventModel(
            id=uuid4(),
            event_id=f"diddigo:driver-access:{user_id}:{uuid4()}",
            user_id=user_id,
            access_status=access_status,
            enabled_at=enabled_at,
            reason=reason[:180],
            source=source,
            status="pending",
            attempts=0,
            next_attempt_at=now,
            created_at=now,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_due(self, *, now: datetime, limit: int) -> list[orm.DriverAccessStatusEventModel]:
        result = await self._session.execute(
            select(orm.DriverAccessStatusEventModel)
            .where(
                orm.DriverAccessStatusEventModel.status.in_(["pending", "retry"]),
                orm.DriverAccessStatusEventModel.next_attempt_at <= now,
            )
            # Oldest first, so the statuses of one driver reach DiddiFreeID in order.
            .order_by(orm.DriverAccessStatusEventModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def mark_delivered(self, event: orm.DriverAccessStatusEventModel, *, now: datetime) -> None:
        event.status = "delivered"
        event.attempts += 1
        event.delivered_at = now
        event.last_error = None
        await self._session.flush()

    async def mark_retry(
        self, event: orm.DriverAccessStatusEventModel, *, next_attempt_at: datetime, error: str
    ) -> None:
        event.status = "retry"
        event.attempts += 1
        event.next_attempt_at = next_attempt_at
        event.last_error = error[:2000]
        await self._session.flush()

    async def mark_refused(self, event: orm.DriverAccessStatusEventModel, *, error: str) -> None:
        """Refused for good by DiddiFreeID (4xx): kept for a human, never resent."""
        event.status = "refused"
        event.attempts += 1
        event.last_error = error[:2000]
        await self._session.flush()

    async def has_waiting_before(self, event: orm.DriverAccessStatusEventModel) -> bool:
        """True when an older status of the same driver is still not delivered (keep the order)."""
        result = await self._session.execute(
            select(orm.DriverAccessStatusEventModel.id)
            .where(
                orm.DriverAccessStatusEventModel.user_id == event.user_id,
                orm.DriverAccessStatusEventModel.created_at < event.created_at,
                orm.DriverAccessStatusEventModel.status.in_(["pending", "retry"]),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
