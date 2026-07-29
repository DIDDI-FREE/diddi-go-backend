"""Auth domain entities — plain dataclasses, no SQLAlchemy dependency.

Clean architecture rule: `app_base/modules/auth/domain/` depends on nothing
outside itself. SQLAlchemy models in `auth/infra/models.py` are the ORM
projection of these entities and are never imported from `domain/`.

Note: instances are mutable (`frozen=False`) — the service layer assigns
e.g. `user.status = "active"` after OTP verification. Immutability is a
nice-to-have that would require every mutation to rebuild a new instance;
we can tighten this once the domain logic settles.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class UserRole(str, Enum):
    PASSENGER = "passenger"
    DRIVER = "driver"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


@dataclass
class User:
    id: UUID
    phone: str
    role: UserRole
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    full_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class OtpCode:
    """One-time-password record. Consumed (or expired) records are kept for
    audit but no longer valid for verification."""

    id: UUID
    phone: str
    code_hash: str
    expires_at: datetime
    created_at: datetime
    consumed_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()
