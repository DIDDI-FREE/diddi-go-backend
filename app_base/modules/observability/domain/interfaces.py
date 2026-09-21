from __future__ import annotations

from datetime import datetime
from typing import Protocol


class OperationalLogRepository(Protocol):
    async def search(
        self,
        *,
        field: str,
        value: str,
        start: datetime,
        end: datetime,
        level: str | None,
        limit: int,
        cursor: str | None,
    ) -> dict: ...
