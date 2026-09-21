from __future__ import annotations

from typing import Protocol
from uuid import UUID


class CapabilityStatusPublisher(Protocol):
    async def publish_driver_status(
        self,
        user_id: UUID,
        *,
        operational_status: str,
        actions: list[str],
    ) -> bool: ...
