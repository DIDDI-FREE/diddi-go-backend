"""Background reconciliation of DiddiPay payments.

DiddiPay's callback is the fast path, not the reliable one. A webhook is lost
whenever DiddiGo is redeploying, the HMAC secret is rotated mid-flight, or the
POST simply never lands — and the payment then sits in `requires_action`
forever even though the passenger paid. This module re-reads
`GET /payfund/v1/payment-intents/{payment_intent_id}` for every intent still
awaiting a callback and replays the transition the webhook would have applied.

Three entry points, one implementation:
  - `reconciliation_loop` — the periodic sweep started by the lifespan
  - `run_reconciliation_once` — a single sweep, used by the loop, the admin
    endpoint and `python -m app_base.tools.reconcile_payments`
  - `PaymentService.reconcile_pending` — the logic itself, provider-agnostic
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from uuid import uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker

from app_base.core.database import async_session_factory
from app_base.core.settings import settings
from app_base.modules.payment.application.services import PaymentService, ReconciliationReport
from app_base.modules.payment.infra.diddipay_client import DiddiPayClient
from app_base.modules.payment.infra.repositories import SqlAlchemyPaymentRepository
from app_base.modules.ride.infra.repositories import SqlAlchemyRideRepository

logger = logging.getLogger(__name__)

LOCK_KEY = "diddigo:payment:reconciliation:lock"

# Lua so the release cannot delete a lock that already expired and was taken by
# another replica mid-sweep.
_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


async def run_reconciliation_once(
    *,
    session_factory: async_sessionmaker | None = None,
    limit: int | None = None,
) -> ReconciliationReport:
    """Run one sweep in its own session and commit whatever it repaired."""
    factory = session_factory or async_session_factory
    async with factory() as session:
        service = PaymentService(
            payment_repo=SqlAlchemyPaymentRepository(session),
            ride_repo=SqlAlchemyRideRepository(session),
            diddipay=DiddiPayClient(),
        )
        try:
            report = await service.reconcile_pending(limit=limit)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    return report


async def reconciliation_loop(redis: Redis | None = None) -> None:
    """Sweep every `payment_reconciliation_interval_seconds` until cancelled.

    Sleeps first: startup is the worst moment to hit DiddiPay, and anything
    already stale will still be stale one interval later.
    """
    interval = max(30, settings.payment_reconciliation_interval_seconds)
    logger.info("payment reconciliation loop started (interval=%ss)", interval)
    while True:
        try:
            await asyncio.sleep(interval)
            await _run_guarded(redis, ttl_seconds=interval)
        except asyncio.CancelledError:
            logger.info("payment reconciliation loop stopped")
            raise
        except Exception:
            # A failed sweep must never kill the loop — the next one retries.
            logger.exception("payment reconciliation sweep failed")


async def _run_guarded(redis: Redis | None, *, ttl_seconds: int) -> None:
    """Run a sweep while holding the cross-replica lock, if Redis is available.

    Two replicas reconciling the same intents is not corrupting — every write
    is idempotent — but it doubles the load on DiddiPay for no benefit.
    """
    if not (settings.diddipay_base_url and settings.diddipay_service_key):
        logger.debug("payment reconciliation skipped — DiddiPay is not configured")
        return

    if redis is None:
        await _log_report(await run_reconciliation_once())
        return

    token = str(uuid4())
    acquired = await redis.set(LOCK_KEY, token, nx=True, ex=ttl_seconds)
    if not acquired:
        logger.debug("payment reconciliation skipped — another replica holds the lock")
        return
    try:
        await _log_report(await run_reconciliation_once())
    finally:
        with contextlib.suppress(Exception):
            await redis.eval(_RELEASE_SCRIPT, 1, LOCK_KEY, token)


async def _log_report(report: ReconciliationReport) -> None:
    if report.checked == 0:
        logger.debug("payment reconciliation found nothing to check")
        return
    log = logger.warning if (report.errors or report.mismatched or report.missing) else logger.info
    log(
        "payment reconciliation checked=%d updated=%d unchanged=%d missing=%d mismatched=%d errors=%d",
        report.checked,
        report.updated,
        report.unchanged,
        report.missing,
        report.mismatched,
        report.errors,
    )
