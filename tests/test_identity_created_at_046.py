"""Ticket 046: DiddiFreeID profile `created_at` (ISO text). Real Postgres.

- A readable date is stored as the new user's creation date.
- Missing, unreadable, or no profile: a new user is refused with 502 IDENTITY_PROFILE_INVALID
  and a message that says exactly what is wrong. Nothing is saved.
- A user who already exists logs in normally: the date is never used again.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app_base.core.auth_deps import _upsert_identity_shadow_user
from app_base.core.database import async_session_factory, engine
from app_base.core.errors import ApiError
from app_base.core.identity import identity_payload_to_user_model
from app_base.modules.auth.infra import models as auth_orm
from app_base.modules.auth.infra.repositories import SqlAlchemyUserRepository


def _user(profile):
    payload = {"sub": str(uuid4()), "role": "user", "status": "active"}
    return identity_payload_to_user_model(payload, profile)


def _profile(**extra):
    return {"phone": f"+22507{uuid4().int % 10**8:08d}", "full_name": "Test", **extra}


async def _login(user) -> None:
    async with async_session_factory() as session:
        await _upsert_identity_shadow_user(user, SqlAlchemyUserRepository(session))


async def _stored(user_id):
    async with async_session_factory() as session:
        return await session.get(auth_orm.UserModel, user_id)


@pytest.mark.asyncio
async def test_new_user_with_iso_text_date_logs_in_with_that_date() -> None:
    user = _user(_profile(created_at="2026-09-21T13:00:00Z"))
    await _login(user)
    row = await _stored(user.id)
    assert row is not None
    assert row.created_at == datetime(2026, 9, 21, 13, 0, tzinfo=UTC)
    await engine.dispose()


@pytest.mark.parametrize(
    ("profile", "problem", "words"),
    [
        (_profile(), "missing", "ne contient pas le champ created_at"),
        (_profile(created_at=None), "missing", "ne contient pas le champ created_at"),
        (_profile(created_at="21/09/2026"), "unreadable", "'21/09/2026', qui n'est pas une date ISO 8601"),
        (_profile(created_at="2026-09-21T13:00:00"), "unreadable", "n'a pas de fuseau horaire"),
        (_profile(created_at=1695301200), "unreadable", "n'est pas un texte de date mais int"),
        (None, "profile_missing", "aucun profil"),
    ],
)
@pytest.mark.asyncio
async def test_new_user_with_a_bad_date_is_refused_with_the_exact_reason(profile, problem, words) -> None:
    user = _user(profile)
    with pytest.raises(ApiError) as excinfo:
        await _login(user)
    error = excinfo.value
    assert error.status_code == 502 and error.code == "IDENTITY_PROFILE_INVALID"
    assert words in error.message
    assert error.details["field"] == "created_at" and error.details["problem"] == problem
    assert await _stored(user.id) is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_existing_user_still_logs_in_whatever_the_profile_says() -> None:
    first = _user(_profile(created_at="2026-09-21T13:00:00Z"))
    await _login(first)

    again = identity_payload_to_user_model(
        {"sub": str(first.id), "role": "user", "status": "active"}, _profile(created_at="garbage")
    )
    await _login(again)

    row = await _stored(first.id)
    assert row.created_at == datetime(2026, 9, 21, 13, 0, tzinfo=UTC)
    await engine.dispose()
