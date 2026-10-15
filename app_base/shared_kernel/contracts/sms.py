from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SmsDelivery:
    provider: str
    status: str
    message_id: str | None = None


class SmsProvider(Protocol):
    async def send(
        self,
        *,
        recipient: str,
        message: str,
        idempotency_key: str,
    ) -> SmsDelivery: ...

    async def close(self) -> None: ...
