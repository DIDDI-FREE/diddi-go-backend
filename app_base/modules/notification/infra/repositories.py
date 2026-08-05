from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.notification.domain import UserDevice
from app_base.modules.notification.infra.models import UserDeviceModel


class SqlAlchemyUserDeviceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, device: UserDevice) -> UserDevice:
        result = await self._session.execute(
            select(UserDeviceModel).where(UserDeviceModel.push_token == device.push_token),
        )
        row = result.scalar_one_or_none()
        now = datetime.now(UTC)
        if row is None:
            row = UserDeviceModel(id=device.id)
            self._session.add(row)
            row.created_at = now
        row.user_id = device.user_id
        row.platform = device.platform
        row.push_provider = device.push_provider
        row.push_token = device.push_token
        row.device_id = device.device_id
        row.enabled = True
        row.last_seen_at = now
        row.updated_at = now
        await self._session.flush()
        return self._to_domain(row)

    async def disable(self, *, user_id: UUID, push_token: str) -> None:
        result = await self._session.execute(
            select(UserDeviceModel).where(
                UserDeviceModel.user_id == user_id,
                UserDeviceModel.push_token == push_token,
            ),
        )
        row = result.scalar_one_or_none()
        if row is not None:
            row.enabled = False
            row.updated_at = datetime.now(UTC)
            await self._session.flush()

    async def active_for_user(self, user_id: UUID) -> list[UserDevice]:
        result = await self._session.execute(
            select(UserDeviceModel).where(
                UserDeviceModel.user_id == user_id,
                UserDeviceModel.enabled.is_(True),
            ),
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    @staticmethod
    def _to_domain(row: UserDeviceModel) -> UserDevice:
        return UserDevice(
            id=row.id,
            user_id=row.user_id,
            platform=row.platform,
            push_provider=row.push_provider,
            push_token=row.push_token,
            device_id=row.device_id,
            enabled=row.enabled,
            last_seen_at=row.last_seen_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
