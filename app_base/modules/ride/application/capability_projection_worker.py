"""Background delivery and reconciliation loop for driver projections."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app_base.core.database import async_session_factory
from app_base.core.metrics import set_value
from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.ride.application.capability_projection import (
    DriverCapabilityProjectionDispatcher,
)
from app_base.modules.ride.infra.capability_projection_repository import (
    SqlAlchemyDriverCapabilityProjectionRepository,
)
from app_base.modules.ride.infra.driver_location import RedisDriverLocationService
from app_base.modules.ride.infra.identity_capability_client import IdentityCapabilityClient

logger = logging.getLogger(__name__)


async def capability_projection_loop(
    client: IdentityCapabilityClient,
    locations: RedisDriverLocationService,
) -> None:
    next_reconciliation = datetime.now(UTC)
    while True:
        try:
            async with async_session_factory() as session:
                repository = SqlAlchemyDriverCapabilityProjectionRepository(session)
                dispatcher = DriverCapabilityProjectionDispatcher(
                    repository,
                    client,
                    retry_base_seconds=settings.capability_projection_retry_base_seconds,
                    retry_max_seconds=settings.capability_projection_retry_max_seconds,
                )
                await dispatcher.deliver_due(batch_size=settings.capability_projection_batch_size)
                projection_metrics = await repository.projection_metrics(now=datetime.now(UTC))
                for status in ("pending", "retry", "conflict", "succeeded"):
                    set_value("diddigo_capability_projection_backlog", 0, {"status": status})
                for key, value in projection_metrics.items():
                    if key.startswith("status:"):
                        set_value(
                            "diddigo_capability_projection_backlog",
                            value,
                            {"status": key.removeprefix("status:")},
                        )
                    else:
                        set_value("diddigo_capability_projection_last_success_age_seconds", value)
                await session.commit()

            now = datetime.now(UTC)
            if now >= next_reconciliation:
                await _reconcile(client, locations)
                next_reconciliation = now + timedelta(
                    seconds=settings.capability_projection_reconciliation_interval_seconds,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Capability projection worker iteration failed")
            log_event(
                "identity.capability.projection.worker_failed",
                level="error",
                error_type=type(exc).__name__,
            )
        await asyncio.sleep(settings.capability_projection_delivery_interval_seconds)


async def _reconcile(
    client: IdentityCapabilityClient,
    locations: RedisDriverLocationService,
) -> None:
    async with async_session_factory() as session:
        repository = SqlAlchemyDriverCapabilityProjectionRepository(session)
        candidates = []
        offset = 0
        while True:
            page = await repository.list_candidates(
                limit=settings.capability_projection_batch_size,
                offset=offset,
            )
            candidates.extend(page)
            if len(page) < settings.capability_projection_batch_size:
                break
            offset += len(page)
        online_user_ids = {
            candidate.user_id
            for candidate in candidates
            if await locations.is_online_and_available(candidate.user_id)
        }
        dispatcher = DriverCapabilityProjectionDispatcher(repository, client)
        await dispatcher.reconcile(
            candidates=candidates,
            online_user_ids=online_user_ids,
            refresh_before=datetime.now(UTC) - timedelta(seconds=settings.capability_projection_refresh_seconds),
            batch_size=settings.capability_projection_batch_size,
        )
        await session.commit()
