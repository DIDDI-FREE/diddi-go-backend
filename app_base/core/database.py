"""Async SQLAlchemy engine + session factory.

The engine is instantiated once at module import from `settings.database_url`.
Routes obtain a session via the `get_session` FastAPI dependency declared in
`app_base.core.deps`.

Migration ownership: Alembic. `init_db()` no longer calls `create_all` — that
role belongs to `alembic upgrade head`. The lifespan calls `ping_db()` only to
surface connection problems early.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app_base.core.settings import settings

logger = logging.getLogger(__name__)


engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=(settings.environment == "debug"),
)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def ping_db() -> None:
    """Best-effort connectivity check at startup.

    Raises if the DB is unreachable; the lifespan logs and the app refuses to
    start — which is the correct fail-loud behavior for a missing database
    during local development.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("database reachable at %s", settings.database_url.split("@", 1)[-1])
    except Exception:
        logger.exception("database NOT reachable at %s", settings.database_url.split("@", 1)[-1])
        raise


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. Yields one AsyncSession per request; commits if the
    handler completes without raising, rolls back otherwise.

    IMPORTANT — this commit is a safety net, not the primary one. FastAPI
    closes dependencies *after* the response has been handed to the client, so
    a caller acting on the response can issue its next request before this
    commit lands. That is a real race for write endpoints: `POST
    /auth/otp/verify` returns a token, and a client using it immediately would
    otherwise be authenticated against a user still stored as
    `pending_verification`, getting a spurious `403 USER_SUSPENDED`.

    Write use cases must therefore commit explicitly before returning (see
    `AuthService.verify_otp`). This teardown then commits nothing and simply
    ends the transaction, which also keeps pooled connections clean.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
