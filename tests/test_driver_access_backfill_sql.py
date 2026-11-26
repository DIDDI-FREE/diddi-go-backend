"""Ticket 084 on real Postgres: the access status queue and the one-time back-fill."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app_base.core.database import async_session_factory, engine
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.application.driver_service import KYC_DOCUMENT_TYPES
from app_base.modules.ride.infra import models as orm
from app_base.modules.ride.infra.driver_access_repository import SqlAlchemyDriverAccessStatusRepository
from app_base.tools import backfill_driver_access_status as backfill


def _history(when: str) -> list[dict]:
    return [{"document_type": doc, "status": "approved", "reviewed_at": when} for doc in KYC_DOCUMENT_TYPES]


async def _driver(*, status="active", history=None, license_verified_at=None, created_at=None):
    user_id, driver_id = uuid4(), uuid4()
    async with async_session_factory() as session:
        session.add(UserModel(id=user_id, phone=f"+225{user_id.int % 10_000_000_000:010d}", role="user"))
        await session.flush()
        row = orm.DriverProfileModel(
            id=driver_id, user_id=user_id, license_number=f"LIC-{driver_id.hex[:12]}", status=status,
            kyc_review_history=history or [], license_verified_at=license_verified_at,
        )
        if created_at is not None:
            row.created_at = created_at
        session.add(row)
        await session.commit()
    return user_id, driver_id


def _ours(report, ids):
    return {item["driver_id"]: item for item in report["drivers"] if item["driver_id"] in {str(i) for i in ids}}


async def _queued(user_id):
    async with async_session_factory() as session:
        rows = (await session.execute(
            select(orm.DriverAccessStatusEventModel).where(orm.DriverAccessStatusEventModel.user_id == user_id)
        )).scalars().all()
    return rows


@pytest.mark.asyncio
async def test_backfill_dates_dry_run_apply_and_rerun() -> None:
    with_history = await _driver(history=_history("2026-03-02T08:00:00+00:00"))
    last_only = await _driver(license_verified_at=datetime(2026, 4, 1, 9, tzinfo=UTC))
    created_only = await _driver(created_at=datetime(2026, 5, 1, 7, tzinfo=UTC))
    recent = await _driver(history=_history("2026-11-25T21:46:59+00:00"))
    pending = await _driver(status="pending_verification")
    ids = [d for _, d in (with_history, last_only, created_only, recent, pending)]

    dry = _ours(await backfill.run(apply=False, include_recent=False), ids)
    assert str(pending[1]) not in dry  # only active drivers
    assert dry[str(with_history[1])]["date_source"] == "first_approval_in_history"
    assert dry[str(with_history[1])]["enabled_at"].startswith("2026-03-02T08:00:00")
    assert dry[str(last_only[1])]["date_source"] == "last_approval_date"
    assert dry[str(created_only[1])]["date_source"] == "driver_created_at"
    assert dry[str(recent[1])]["action"] == "skip_recent"
    assert await _queued(with_history[0]) == []  # dry run changes nothing

    await backfill.run(apply=True, include_recent=False)
    queued = await _queued(with_history[0])
    assert len(queued) == 1
    assert queued[0].access_status == "enabled" and queued[0].source == "backfill"
    assert queued[0].enabled_at == datetime(2026, 3, 2, 8, tzinfo=UTC)
    assert await _queued(recent[0]) == []

    again = _ours(await backfill.run(apply=True, include_recent=True), ids)
    assert again[str(with_history[1])]["action"] == "skip_already_backfilled"
    assert len(await _queued(with_history[0])) == 1
    assert len(await _queued(recent[0])) == 1  # newcomer queued only with --include-recent
    await engine.dispose()


@pytest.mark.asyncio
async def test_queue_order_and_last_status() -> None:
    user_id, _ = await _driver()
    async with async_session_factory() as session:
        repo = SqlAlchemyDriverAccessStatusRepository(session)
        first = await repo.enqueue(
            user_id=user_id, access_status="enabled", reason="kyc_approved", source="kyc",
            now=datetime(2026, 11, 26, 8, tzinfo=UTC),
        )
        second = await repo.enqueue(
            user_id=user_id, access_status="suspended", reason="kyc_rejected", source="kyc",
            now=datetime(2026, 11, 26, 9, tzinfo=UTC),
        )
        assert await repo.last_status(user_id) == "suspended"
        assert await repo.has_waiting_before(second) is True
        await repo.mark_delivered(first, now=datetime.now(UTC))
        assert await repo.has_waiting_before(second) is False
        await session.commit()
    await engine.dispose()
