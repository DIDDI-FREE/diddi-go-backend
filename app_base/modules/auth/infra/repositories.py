"""SQLAlchemy-backed auth repositories (batch 5 infrastructure, batch 6
swaps the in-memory service for DB-backed logic using these).

Two repo classes matching `auth/domain/interfaces.py` protocols:
    SqlAlchemyUserRepository   → UserRepository
    SqlAlchemyOTPRepository    → OTPRepository

The ORM `User` ↔ SQLAlchemy `UserModel` translation lives entirely inside
these classes so the domain layer never sees SQLAlchemy types.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.auth.domain.entities import (
    OtpCode,
    User,
    UserRole,
    UserStatus,
)
from app_base.modules.auth.domain.interfaces import (
    OTPRepository,
    UserRepository,
)
from app_base.modules.auth.infra import models as orm


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        """Make pending writes visible to other connections *now*.

        Needed because FastAPI tears dependencies down after the response is
        sent: a client that acts on the response immediately would otherwise
        race the session teardown's commit. See `get_session`.
        """
        await self._session.commit()

    async def save(self, user: User) -> User:
        row: orm.UserModel | None = await self._session.get(orm.UserModel, user.id)
        if row is None:
            row = orm.UserModel(
                id=user.id,
                phone=user.phone,
                full_name=user.full_name,
                role=user.role.value if isinstance(user.role, UserRole) else user.role,
                status=user.status.value if isinstance(user.status, UserStatus) else user.status,
                created_at=user.created_at or datetime.now(UTC),
                updated_at=user.updated_at or datetime.now(UTC),
            )
            self._session.add(row)
        else:
            row.full_name = user.full_name
            row.role = user.role.value if isinstance(user.role, UserRole) else user.role
            row.status = user.status.value if isinstance(user.status, UserStatus) else user.status
            row.updated_at = datetime.now(UTC)
        await self._session.flush()
        return user

    async def find_by_id(self, user_id: UUID) -> User | None:
        # `session.get()` would answer from the identity map when the instance
        # is already loaded. Combined with `expire_on_commit=False` on the
        # session factory, that can hand back a row from before the user was
        # activated — authentication then rejects a perfectly valid token with
        # `USER_SUSPENDED`. `populate_existing()` forces a real SELECT and
        # refreshes the cached instance from the database.
        result = await self._session.execute(
            select(orm.UserModel)
            .where(orm.UserModel.id == user_id)
            .execution_options(populate_existing=True),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def find_by_phone(self, phone: str) -> User | None:
        # Same staleness concern as `find_by_id` — the OTP flow reads a user by
        # phone immediately after another request activated them.
        result = await self._session.execute(
            select(orm.UserModel)
            .where(orm.UserModel.phone == phone)
            .execution_options(populate_existing=True),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: orm.UserModel) -> User:
        return User(
            id=row.id,
            phone=row.phone,
            full_name=row.full_name,
            role=UserRole(row.role),
            status=UserStatus(row.status),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class SqlAlchemyOTPRepository(OTPRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        """See `SqlAlchemyUserRepository.commit`."""
        await self._session.commit()

    async def save(self, otp: OtpCode) -> OtpCode:
        row = orm.OtpCodeModel(
            id=otp.id,
            phone=otp.phone,
            code_hash=otp.code_hash,
            expires_at=otp.expires_at,
            created_at=otp.created_at,
            consumed_at=otp.consumed_at,
        )
        self._session.add(row)
        await self._session.flush()
        return otp

    async def find_latest_unconsumed(self, phone: str) -> OtpCode | None:
        result = await self._session.execute(
            select(orm.OtpCodeModel)
            .where(
                orm.OtpCodeModel.phone == phone,
                orm.OtpCodeModel.consumed_at.is_(None),
            )
            .order_by(orm.OtpCodeModel.created_at.desc())
            .limit(1),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return OtpCode(
            id=row.id,
            phone=row.phone,
            code_hash=row.code_hash,
            expires_at=row.expires_at,
            created_at=row.created_at,
            consumed_at=row.consumed_at,
        )

    async def mark_consumed(self, otp_id: UUID) -> None:
        row = await self._session.get(orm.OtpCodeModel, otp_id)
        if row is None or row.consumed_at is not None:
            return
        row.consumed_at = datetime.now(UTC)
        await self._session.flush()
