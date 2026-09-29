"""SQLAlchemy dispatch-config store (SCRUM-63 / UC-288).

The single effective ``ride.dispatch_config`` row holds the tunables an
operator can edit without a redeploy. Settings seed the defaults so the engine
works before the row exists and stays sane if the table is empty.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.settings import Settings
from app_base.modules.ride.application.dispatch_config import dispatch_config_from_settings
from app_base.modules.ride.domain.priority import DispatchConfig
from app_base.modules.ride.infra import models as orm


def _to_config(row: orm.DispatchConfigModel) -> DispatchConfig:
    return DispatchConfig(
        search_radius_km=float(row.search_radius_km),
        search_radius_step_km=float(row.search_radius_step_km),
        search_radius_max_km=float(row.search_radius_max_km),
        offer_wave_size=row.offer_wave_size,
        search_budget_seconds=row.search_budget_seconds,
        eta_shortlist_size=row.eta_shortlist_size,
        priority_window_days=row.priority_window_days,
        priority_cap_seconds=row.priority_cap_seconds,
        priority_seconds_per_point=row.priority_seconds_per_point,
        points_ride_completed=row.points_ride_completed,
        points_ride_cancelled_by_driver=row.points_ride_cancelled_by_driver,
    )


class SqlAlchemyDispatchConfigStore:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def _row(self) -> orm.DispatchConfigModel | None:
        result = await self._session.execute(
            select(orm.DispatchConfigModel).order_by(orm.DispatchConfigModel.updated_at.desc()).limit(1),
        )
        return result.scalar_one_or_none()

    async def load(self) -> DispatchConfig:
        row = await self._row()
        return _to_config(row) if row is not None else dispatch_config_from_settings(self._settings)

    async def save(self, config: DispatchConfig) -> DispatchConfig:
        row = await self._row()
        values = {
            "search_radius_km": Decimal(str(config.search_radius_km)),
            "search_radius_step_km": Decimal(str(config.search_radius_step_km)),
            "search_radius_max_km": Decimal(str(config.search_radius_max_km)),
            "offer_wave_size": config.offer_wave_size,
            "search_budget_seconds": config.search_budget_seconds,
            "eta_shortlist_size": config.eta_shortlist_size,
            "priority_window_days": config.priority_window_days,
            "priority_cap_seconds": config.priority_cap_seconds,
            "priority_seconds_per_point": config.priority_seconds_per_point,
            "points_ride_completed": config.points_ride_completed,
            "points_ride_cancelled_by_driver": config.points_ride_cancelled_by_driver,
        }
        if row is None:
            self._session.add(orm.DispatchConfigModel(**values))
        else:
            for field, value in values.items():
                setattr(row, field, value)
        return config
