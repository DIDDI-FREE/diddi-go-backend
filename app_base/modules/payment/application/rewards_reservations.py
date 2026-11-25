"""Background sweep that closes DiddiRewards reservations left open (ticket 014).

A reservation holds part of the passenger's entitlement and of the campaign
budget until DiddiGo confirms or releases it. Both calls are best-effort on the
request path, so this sweep retries them until Rewards answers:
  - a release that failed (`release_deferred`) or never left (ride abandoned);
  - a confirm that failed after the ride was paid. A confirm Rewards refuses for
    good is ended by a release inside `PaymentService`.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app_base.core.database import async_session_factory
from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.core.telemetry import worker_iteration
from app_base.modules.payment.application.services import PaymentService
from app_base.modules.payment.domain.entities import PaymentStatus
from app_base.modules.payment.infra.repositories import SqlAlchemyPaymentRepository
from app_base.modules.ride.application.rewards_release import (
    ABANDONED_RIDE_STATUSES,
    release_reason,
    release_reservation,
)
from app_base.modules.ride.domain.entities import RideStatus
from app_base.modules.ride.infra.repositories import SqlAlchemyRideRepository

logger = logging.getLogger(__name__)

WORKER_NAME = "rewards-reservations"
SWEEP_INTERVAL_SECONDS = 60
# Rewards itself expires a reservation after 24 h; older rides have nothing left to close.
SWEEP_WINDOW = timedelta(days=7)
SWEEP_LIMIT = 200
LOCK_KEY = "diddigo:rewards:reservations:lock"

_RELEASE_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


async def run_rewards_reservations_once(
    diddirewards: Any,
    *,
    session_factory: async_sessionmaker | None = None,
    limit: int = SWEEP_LIMIT,
) -> dict[str, int]:
    """One sweep. Each ride is committed on its own so one failure does not undo the others."""
    report = {"checked": 0, "released": 0, "confirmed": 0, "errors": 0}
    factory = session_factory or async_session_factory
    async with factory() as session:
        ride_repo = SqlAlchemyRideRepository(session)
        payment_repo = SqlAlchemyPaymentRepository(session)
        payments = PaymentService(payment_repo=payment_repo, ride_repo=ride_repo, diddirewards=diddirewards)
        rides = await ride_repo.list_open_rewards_reservations(
            since=datetime.now(UTC) - SWEEP_WINDOW, limit=limit
        )
        for ride in rides:
            report["checked"] += 1
            try:
                outcome = await close_reservation(
                    ride, diddirewards=diddirewards, ride_repo=ride_repo, payment_repo=payment_repo, payments=payments
                )
                if outcome:
                    report[outcome] += 1
                await session.commit()
            except Exception:
                await session.rollback()
                report["errors"] += 1
                logger.exception("rewards reservation sweep failed ride_id=%s", ride.id)
    return report


async def close_reservation(
    ride: Any, *, diddirewards: Any, ride_repo: Any, payment_repo: Any, payments: PaymentService
) -> str | None:
    """Try to end one open reservation. Returns "released", "confirmed" or None (nothing done yet)."""
    must_release = ride.rewards_status == "release_deferred" or ride.status in ABANDONED_RIDE_STATUSES
    reason = release_reason(ride)
    if must_release or reason == "nothing_reserved":
        if reason and await release_reservation(diddirewards, ride_repo, ride, reason=reason):
            return "released"
        return None
    if ride.status is RideStatus.COMPLETED:
        payment = await payment_repo.find_by_ride_id(ride.id)
        if payment is not None and payment.status in {PaymentStatus.COLLECTED, PaymentStatus.SUCCEEDED}:
            await payments.retry_rewards_confirmation(ride, payment)
            if ride.rewards_status == "confirmed":
                return "confirmed"
            if ride.rewards_status == "confirmation_refused":
                return "released"
    return None


async def rewards_reservations_loop(diddirewards: Any, redis: Redis | None = None) -> None:
    logger.info("rewards reservations loop started (interval=%ss)", SWEEP_INTERVAL_SECONDS)
    while True:
        try:
            await asyncio.sleep(SWEEP_INTERVAL_SECONDS)
            with worker_iteration(WORKER_NAME):
                await _run_guarded(diddirewards, redis)
        except asyncio.CancelledError:
            logger.info("rewards reservations loop stopped")
            raise
        except Exception:
            # A failed sweep must never kill the loop: the next one retries.
            logger.exception("rewards reservations sweep failed")


async def _run_guarded(diddirewards: Any, redis: Redis | None) -> None:
    """Run one sweep under a cross-replica lock when Redis is there (calls are idempotent anyway)."""
    if not (settings.diddi_rewards_enabled and getattr(diddirewards, "configured", False)):
        return
    if redis is None:
        _log_report(await run_rewards_reservations_once(diddirewards))
        return
    token = str(uuid4())
    if not await redis.set(LOCK_KEY, token, nx=True, ex=SWEEP_INTERVAL_SECONDS):
        return
    try:
        _log_report(await run_rewards_reservations_once(diddirewards))
    finally:
        with contextlib.suppress(Exception):
            await redis.eval(_RELEASE_LOCK_SCRIPT, 1, LOCK_KEY, token)


def _log_report(report: dict[str, int]) -> None:
    if report["released"] or report["confirmed"] or report["errors"]:
        log_event("rewards.reservations.sweep", level="error" if report["errors"] else "info", **report)
