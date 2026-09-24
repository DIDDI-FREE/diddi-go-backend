"""PostgreSQL outbox for DiddiFreeID driver capability projections."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.ride.domain.capability_projection import (
    DriverCapabilityProjectionEvent,
    DriverProjectionCandidate,
)
from app_base.modules.ride.infra.models import (
    DriverCapabilityProjectionEventModel,
    DriverCapabilityProjectionStateModel,
    DriverProfileModel,
    VehicleModel,
)


class SqlAlchemyDriverCapabilityProjectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(
        self,
        user_id: UUID,
        *,
        operational_status: str,
        actions: list[str],
        request_id: str | None,
    ) -> DriverCapabilityProjectionEvent | None:
        await self._session.execute(
            insert(DriverCapabilityProjectionStateModel)
            .values(user_id=user_id, projection_version=0, desired_actions=[])
            .on_conflict_do_nothing(index_elements=["user_id"]),
        )
        state = (
            await self._session.execute(
                select(DriverCapabilityProjectionStateModel)
                .where(DriverCapabilityProjectionStateModel.user_id == user_id)
                .with_for_update(),
            )
        ).scalar_one()
        normalized_actions = list(dict.fromkeys(actions))
        if (
            state.desired_operational_status == operational_status
            and list(state.desired_actions or []) == normalized_actions
            and state.last_event_id
        ):
            return None

        version = int(state.projection_version) + 1
        event_uuid = uuid4()
        event_id = f"diddigo:driver:{user_id}:{version}:{event_uuid}"
        now = datetime.now(UTC)
        row = DriverCapabilityProjectionEventModel(
            id=event_uuid,
            event_id=event_id,
            user_id=user_id,
            projection_version=version,
            operational_status=operational_status,
            actions=normalized_actions,
            request_id=request_id,
            status="pending",
            attempts=0,
            next_attempt_at=now,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        state.projection_version = version
        state.desired_operational_status = operational_status
        state.desired_actions = normalized_actions
        state.last_event_id = event_id
        state.sync_status = "pending"
        state.last_error = None
        state.updated_at = now
        await self._session.flush()
        return _event(row)

    async def list_due(self, *, now: datetime, limit: int) -> list[DriverCapabilityProjectionEvent]:
        rows = (
            await self._session.execute(
                select(DriverCapabilityProjectionEventModel)
                .where(
                    DriverCapabilityProjectionEventModel.status.in_(["pending", "retry"]),
                    DriverCapabilityProjectionEventModel.next_attempt_at <= now,
                )
                .order_by(DriverCapabilityProjectionEventModel.next_attempt_at)
                .limit(limit)
                .with_for_update(skip_locked=True),
            )
        ).scalars().all()
        return [_event(row) for row in rows]

    async def mark_succeeded(self, event: DriverCapabilityProjectionEvent, *, now: datetime) -> None:
        row, state = await self._locked(event)
        row.status = "succeeded"
        row.attempts += 1
        row.last_attempt_at = now
        row.delivered_at = now
        row.last_error = None
        row.updated_at = now
        if state.last_event_id == event.event_id:
            state.sync_status = "succeeded"
            state.last_attempt_at = now
            state.last_succeeded_at = now
            state.next_refresh_at = None
            state.last_error = None
            state.updated_at = now
        await self._session.flush()

    async def mark_retry(
        self,
        event: DriverCapabilityProjectionEvent,
        *,
        now: datetime,
        next_attempt_at: datetime,
        error: str,
    ) -> None:
        row, state = await self._locked(event)
        row.status = "retry"
        row.attempts += 1
        row.last_attempt_at = now
        row.next_attempt_at = next_attempt_at
        row.last_error = error[:2000]
        row.updated_at = now
        if state.last_event_id == event.event_id:
            state.sync_status = "retry"
            state.last_attempt_at = now
            state.last_error = error[:2000]
            state.updated_at = now
        await self._session.flush()

    async def mark_conflict(self, event: DriverCapabilityProjectionEvent, *, now: datetime, error: str) -> None:
        row, state = await self._locked(event)
        row.status = "conflict"
        row.attempts += 1
        row.last_attempt_at = now
        row.last_error = error[:2000]
        row.updated_at = now
        if state.last_event_id == event.event_id:
            state.sync_status = "conflict"
            state.last_attempt_at = now
            state.last_error = error[:2000]
            state.updated_at = now
        await self._session.flush()

    async def mark_dead_letter(self, event: DriverCapabilityProjectionEvent, *, now: datetime, error: str) -> None:
        row, state = await self._locked(event)
        row.status = "dead_letter"
        row.attempts += 1
        row.last_attempt_at = now
        row.last_error = error[:2000]
        row.updated_at = now
        if state.last_event_id == event.event_id:
            state.sync_status = "dead_letter"
            state.last_attempt_at = now
            state.last_error = error[:2000]
            state.updated_at = now
        await self._session.flush()

    async def schedule_stale_refresh(self, *, before: datetime, now: datetime, limit: int) -> int:
        states = (
            await self._session.execute(
                select(DriverCapabilityProjectionStateModel)
                .where(
                    DriverCapabilityProjectionStateModel.sync_status == "succeeded",
                    DriverCapabilityProjectionStateModel.last_succeeded_at <= before,
                )
                .order_by(DriverCapabilityProjectionStateModel.last_succeeded_at)
                .limit(limit)
                .with_for_update(skip_locked=True),
            )
        ).scalars().all()
        refreshed = 0
        for state in states:
            row = (
                await self._session.execute(
                    select(DriverCapabilityProjectionEventModel).where(
                        DriverCapabilityProjectionEventModel.event_id == state.last_event_id,
                    ),
                )
            ).scalar_one_or_none()
            if row is None:
                continue
            row.status = "pending"
            row.next_attempt_at = now
            row.updated_at = now
            state.sync_status = "pending"
            state.next_refresh_at = now
            state.updated_at = now
            refreshed += 1
        await self._session.flush()
        return refreshed

    async def list_candidates(self, *, limit: int, offset: int = 0) -> list[DriverProjectionCandidate]:
        active_vehicle = (
            select(VehicleModel)
            .where(VehicleModel.driver_id == DriverProfileModel.id)
            .order_by(VehicleModel.active.desc(), VehicleModel.created_at.desc())
            .limit(1)
            .lateral()
        )
        rows = (
            await self._session.execute(
                select(
                    DriverProfileModel.user_id,
                    DriverProfileModel.status,
                    active_vehicle.c.verification_status,
                    active_vehicle.c.active,
                )
                .select_from(DriverProfileModel)
                .outerjoin(active_vehicle, true())
                .order_by(DriverProfileModel.user_id)
                .offset(offset)
                .limit(limit),
            )
        ).all()
        return [
            DriverProjectionCandidate(
                user_id=row[0], profile_status=row[1], vehicle_status=row[2], vehicle_active=row[3],
            )
            for row in rows
        ]

    async def projection_metrics(self, *, now: datetime) -> dict[str, float]:
        counts = (
            await self._session.execute(
                select(
                    DriverCapabilityProjectionEventModel.status,
                    func.count(DriverCapabilityProjectionEventModel.id),
                ).group_by(DriverCapabilityProjectionEventModel.status),
            )
        ).all()
        latest_success = (
            await self._session.execute(
                select(func.max(DriverCapabilityProjectionStateModel.last_succeeded_at)),
            )
        ).scalar_one_or_none()
        metrics = {f"status:{status}": float(count) for status, count in counts}
        metrics["last_success_age_seconds"] = (
            max((now - latest_success).total_seconds(), 0.0) if latest_success else -1.0
        )
        return metrics

    async def _locked(
        self, event: DriverCapabilityProjectionEvent,
    ) -> tuple[DriverCapabilityProjectionEventModel, DriverCapabilityProjectionStateModel]:
        row = (
            await self._session.execute(
                select(DriverCapabilityProjectionEventModel)
                .where(DriverCapabilityProjectionEventModel.id == event.id)
                .with_for_update(),
            )
        ).scalar_one()
        state = (
            await self._session.execute(
                select(DriverCapabilityProjectionStateModel)
                .where(DriverCapabilityProjectionStateModel.user_id == event.user_id)
                .with_for_update(),
            )
        ).scalar_one()
        return row, state


def _event(row: DriverCapabilityProjectionEventModel) -> DriverCapabilityProjectionEvent:
    return DriverCapabilityProjectionEvent(
        id=row.id,
        event_id=row.event_id,
        user_id=row.user_id,
        projection_version=row.projection_version,
        operational_status=row.operational_status,
        actions=list(row.actions or []),
        request_id=row.request_id,
        status=row.status,
        attempts=row.attempts,
        next_attempt_at=row.next_attempt_at,
        created_at=row.created_at,
    )
