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
from app_base.modules.ride.application.capability_projection_worker import capability_projection_loop
from app_base.modules.ride.infra.driver_location import RedisDriverLocationService
from app_base.modules.ride.infra.identity_capability_client import IdentityCapabilityClient
from app_base.modules.ride.infra.routing_client import DiddiMapRoutingClient

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await ping_db()
    app.state.redis = create_redis_pool(settings.redis_url)
    app.state.diddimap = DiddiMapRoutingClient(
        base_url=settings.diddimap_base_url,
        access_token=settings.diddimap_access_token,
        service_client_id=settings.diddimap_service_client_id,
        service_token=settings.diddimap_service_token,
    )
    app.state.driver_locations = RedisDriverLocationService(
        redis=app.state.redis,
        telemetry_ttl_seconds=settings.waiting_telemetry_ttl_seconds,
    )
    app.state.identity_capabilities = IdentityCapabilityClient(
        base_url=settings.identity_base_url,
        client_id=settings.identity_service_client_id,
        client_secret=settings.identity_service_client_secret,
        timeout_seconds=settings.identity_service_timeout_seconds,
    )

    app.state.payment_reconciliation_task = None
    if settings.payment_reconciliation_enabled:
        app.state.payment_reconciliation_task = asyncio.create_task(
            reconciliation_loop(app.state.redis),
            name="payment-reconciliation",
        )

    app.state.capability_projection_task = None
    if settings.capability_projection_enabled:
        app.state.capability_projection_task = asyncio.create_task(
            capability_projection_loop(app.state.identity_capabilities, app.state.driver_locations),
            name="capability-projection",
        )

    logger.info(
        "lifespan startup complete (redis=%s, diddimap=%s, payment_reconciliation=%s, capability_projection=%s)",
        settings.redis_url,
        settings.diddimap_base_url,
        settings.payment_reconciliation_enabled,
        settings.capability_projection_enabled,
    )
    try:
        yield
    finally:
        capability_task: asyncio.Task | None = app.state.capability_projection_task
        if capability_task is not None:
            capability_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await capability_task
        task: asyncio.Task | None = app.state.payment_reconciliation_task
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        diddimap: DiddiMapRoutingClient = app.state.diddimap  # type: ignore[assignment]
        await diddimap.close()
        identity_capabilities: IdentityCapabilityClient = app.state.identity_capabilities  # type: ignore[assignment]
        await identity_capabilities.close()
        await app.state.redis.aclose()
        logger.info("lifespan shutdown complete")
