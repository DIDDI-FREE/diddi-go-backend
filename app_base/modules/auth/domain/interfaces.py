"""Auth domain interfaces — repository + service protocols.

These Protocols are defined here in `domain/` because they describe WHAT
the auth module needs from its data layer, without prescribing HOW. Any
implementation (SQLAlchemy in `auth/infra/repositories.py`, a future
remote call against DiddiFree ID, an in-memory fake for tests) must satisfy
the same interface — which is what makes the auth module extractable as
a standalone service later.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app_base.modules.auth.domain.entities import OtpCode, User


class UserRepository(Protocol):
    async def save(self, user: User) -> User:
        """INSERT or UPDATE. Returns the persisted user (with `id` filled if
        the call site passed a new unsaved instance)."""
        ...

    async def commit(self) -> None:
        """Flush pending writes to the database and make them visible to other
        connections immediately, rather than at request teardown."""
        ...

    async def find_by_id(self, user_id: UUID) -> User | None:
        ...

    async def find_by_phone(self, phone: str) -> User | None:
        ...


class OTPRepository(Protocol):
    async def save(self, otp: OtpCode) -> OtpCode:
        ...

    async def commit(self) -> None:
        """Make pending writes visible immediately — see `UserRepository.commit`."""
        ...

    async def find_latest_unconsumed(self, phone: str) -> OtpCode | None:
        """Returns the newest OTP for `phone` that has not been consumed and
        has not yet expired. None if no such record exists."""
        ...

    async def mark_consumed(self, otp_id: UUID) -> None:
        """Set `consumed_at = now()`. Idempotent — subsequent calls on an
        already-consumed OTP are harmless."""
        ...
