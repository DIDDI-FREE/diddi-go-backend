"""Lifespan context manager wiring startup/shutdown for shared resources.

Startup:
  - verify DB connectivity via `ping_db()`
  - create the shared Redis pool and mount it on `app.state.redis`
  - construct the DiddiMap HTTP routing client and mount it on
    `app.state.diddimap`
  - start the DiddiPay reconciliation sweep, which repairs payments whose
    callback never arrived

Shutdown:
  - cancel the reconciliation task and wait for it to unwind
  - close the Redis pool (redis-py does this cleanly on process exit too,
    but explicit cleanup is polite and avoids test leaks)
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app_base.core.database import ping_db
from app_base.core.redis import create_redis_pool
from app_base.core.settings import settings
from app_base.modules.payment.application.reconciliation import reconciliation_loop
from app_base.modules.ride.infra.driver_location import RedisDriverLocationService
from app_base.modules.ride.infra.routing_client import DiddiMapRoutingClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await ping_db()
    app.state.redis = create_redis_pool(settings.redis_url)
    app.state.diddimap = DiddiMapRoutingClient(base_url=settings.diddimap_base_url)
    app.state.driver_locations = RedisDriverLocationService(redis=app.state.redis)

    app.state.payment_reconciliation_task = None
    if settings.payment_reconciliation_enabled:
        app.state.payment_reconciliation_task = asyncio.create_task(
            reconciliation_loop(app.state.redis),
            name="payment-reconciliation",
        )

    logger.info(
        "lifespan startup complete (redis=%s, diddimap=%s, payment_reconciliation=%s)",
        settings.redis_url,
        settings.diddimap_base_url,
        settings.payment_reconciliation_enabled,
    )
    try:
        yield
    finally:
        task: asyncio.Task | None = app.state.payment_reconciliation_task
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        diddimap: DiddiMapRoutingClient = app.state.diddimap  # type: ignore[assignment]
        await diddimap.close()
        await app.state.redis.aclose()
        logger.info("lifespan shutdown complete")
