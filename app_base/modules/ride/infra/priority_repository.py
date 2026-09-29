"""SQLAlchemy driver priority ledger (SCRUM-63 Phase 3).

Append-only writes and one batched windowed aggregate read. Writes join the
caller's request transaction (no commit here) exactly like the other ride
repositories.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.ride.domain.priority import PriorityEvent, PriorityEventKind
from app_base.modules.ride.infra import models as orm


def _to_event(row: orm.DriverPriorityEventModel) -> PriorityEvent:
    return PriorityEvent(
        driver_id=row.driver_id,
        kind=PriorityEventKind(row.kind),
        points=row.points,
        zone_id=row.zone_id,
        ride_id=row.ride_id,
        reason=row.reason,
        expires_at=row.expires_at,
    )


class SqlAlchemyPriorityLedgerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, event: PriorityEvent) -> None:
        self._session.add(
            orm.DriverPriorityEventModel(
                driver_id=event.driver_id,
                ride_id=event.ride_id,
                zone_id=event.zone_id,
                kind=event.kind.value,
                points=event.points,
                reason=event.reason,
                expires_at=event.expires_at,
            ),
        )

    async def windowed_points(
        self,
        driver_ids: list[UUID],
        *,
        since: datetime,
        zone_id: UUID,
        now: datetime,
    ) -> dict[UUID, int]:
        if not driver_ids:
            return {}
        model = orm.DriverPriorityEventModel
        result = await self._session.execute(
            select(model.driver_id, func.coalesce(func.sum(model.points), 0))
            .where(
                model.driver_id.in_(driver_ids),
                model.created_at > since,
                or_(model.expires_at.is_(None), model.expires_at > now),
                or_(model.zone_id == zone_id, model.zone_id.is_(None)),
            )
            .group_by(model.driver_id),
        )
        return {row[0]: int(row[1]) for row in result.all()}

    async def recent_events(self, driver_id: UUID, *, limit: int = 50) -> list[PriorityEvent]:
        model = orm.DriverPriorityEventModel
        result = await self._session.execute(
            select(model)
            .where(model.driver_id == driver_id)
            .order_by(model.created_at.desc())
            .limit(limit),
        )
        return [_to_event(row) for row in result.scalars().all()]

    async def active_rules(self, *, now: datetime) -> list[PriorityEvent]:
        model = orm.DriverPriorityEventModel
        result = await self._session.execute(
            select(model)
            .where(
                model.kind == PriorityEventKind.TEMP_BOOST.value,
                or_(model.expires_at.is_(None), model.expires_at > now),
            )
            .order_by(model.created_at.desc()),
        )
        return [_to_event(row) for row in result.scalars().all()]
