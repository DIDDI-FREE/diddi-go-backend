"""SQL aggregates for the Pilotage daily ride summary."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.ride.domain.summary import RideSummaryTotals
from app_base.modules.ride.infra.models import RideModel


class SqlAlchemyRideSummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def summarize_period(self, start: datetime, end: datetime) -> RideSummaryTotals:
        requested = (
            select(func.count(RideModel.id))
            .where(RideModel.requested_at >= start, RideModel.requested_at < end)
            .scalar_subquery()
        )
        completed = (
            select(
                func.count(RideModel.id).label("rides_completed"),
                func.coalesce(
                    func.sum(case((RideModel.currency == "XOF", RideModel.final_fare))),
                    0,
                ).label("completed_fare_total_xof"),
                func.count(RideModel.id)
                .filter(RideModel.currency == "XOF", RideModel.final_fare.is_(None))
                .label("completed_rides_without_fare"),
            )
            .where(
                RideModel.status == "completed",
                RideModel.completed_at >= start,
                RideModel.completed_at < end,
            )
            .subquery()
        )
        row = (
            await self._session.execute(
                select(
                    requested.label("rides_requested"),
                    completed.c.rides_completed,
                    completed.c.completed_fare_total_xof,
                    completed.c.completed_rides_without_fare,
                )
            )
        ).one()
        return RideSummaryTotals(
            rides_requested=int(row.rides_requested),
            rides_completed=int(row.rides_completed),
            completed_fare_total_xof=Decimal(row.completed_fare_total_xof),
            completed_rides_without_fare=int(row.completed_rides_without_fare),
        )
