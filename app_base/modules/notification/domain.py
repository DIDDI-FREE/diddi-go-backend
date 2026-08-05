from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class UserDevice:
    id: UUID
    user_id: UUID
    platform: str
    push_provider: str
    push_token: str
    device_id: str | None = None
    enabled: bool = True
    last_seen_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


class UserDeviceRepository(Protocol):
    async def upsert(self, device: UserDevice) -> UserDevice: ...

    async def disable(self, *, user_id: UUID, push_token: str) -> None: ...

    async def active_for_user(self, user_id: UUID) -> list[UserDevice]: ...


class PushGateway(Protocol):
    async def send(
        self,
        *,
        token: str,
        title: str,
        body: str,
        data: dict[str, str],
    ) -> None: ...
