"""Whitelisted SQL aggregations for Pilotage breakdowns."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.ride.domain.breakdown import (
    BreakdownDimension,
    BreakdownItem,
    BreakdownMetric,
)
from app_base.modules.ride.infra.models import RideModel


class SqlAlchemyRideBreakdownRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def aggregate(
        self,
        start: datetime,
        end: datetime,
        dimension: BreakdownDimension,
        metric: BreakdownMetric,
    ) -> tuple[BreakdownItem, ...]:
        timestamp = (
            RideModel.requested_at
            if metric is BreakdownMetric.RIDES_REQUESTED
            else RideModel.completed_at
        )
        dimension_expression = self._dimension_expression(dimension, timestamp)
        value_expression = (
            func.count(RideModel.id)
            if metric is not BreakdownMetric.COMPLETED_FARE_TOTAL_XOF
            else func.coalesce(func.sum(RideModel.final_fare), 0)
        )
        statement = select(
            dimension_expression.label("breakdown_key"),
            value_expression.label("breakdown_value"),
        ).select_from(RideModel)
        statement = statement.where(timestamp >= start, timestamp < end)
        if metric is not BreakdownMetric.RIDES_REQUESTED:
            statement = statement.where(RideModel.status == "completed")
        if metric is BreakdownMetric.COMPLETED_FARE_TOTAL_XOF:
            statement = statement.where(RideModel.currency == "XOF")
        statement = statement.group_by(dimension_expression).order_by(dimension_expression)

        rows = (await self._session.execute(statement)).all()
        return tuple(
            BreakdownItem(key=str(row.breakdown_key), value=Decimal(str(row.breakdown_value)))
            for row in rows
            if row.breakdown_key is not None
        )

    @staticmethod
    def _dimension_expression(dimension: BreakdownDimension, timestamp):
        if dimension is BreakdownDimension.HOUR:
            local_timestamp = func.timezone("Africa/Abidjan", timestamp)
            return func.to_char(local_timestamp, "HH24")
        if dimension is BreakdownDimension.PAYMENT_METHOD:
            return RideModel.payment_method
        if dimension is BreakdownDimension.SERVICE_TYPE:
            return RideModel.vehicle_category
        return RideModel.status
