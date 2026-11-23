"""Durable delivery of DiddiGo Rewards facts to Redis Streams."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis

from app_base.core.database import async_session_factory
from app_base.core.redis import create_redis_pool
from app_base.core.settings import settings
from app_base.core.telemetry import worker_iteration
from app_base.modules.payment.infra.repositories import SqlAlchemyPaymentRepository

logger = logging.getLogger(__name__)


async def run_rewards_events_once(redis: Redis, *, limit: int | None = None) -> int:
    async with async_session_factory() as session:
        repository = SqlAlchemyPaymentRepository(session)
        events = await repository.list_due_rewards_events(
            now=datetime.now(UTC), limit=limit or settings.diddi_rewards_events_batch_size
        )
        delivered = 0
        for event in events:
            try:
                await redis.xadd(
                    settings.diddi_rewards_events_stream,
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "ride_id": str(event.ride_id),
                        "payload": json.dumps(event.payload, separators=(",", ":"), sort_keys=True),
                    },
                )
            except Exception as exc:
                delay = min(
                    settings.diddi_rewards_events_retry_base_seconds * 2 ** min(event.attempts, 8),
                    settings.diddi_rewards_events_retry_max_seconds,
                )
                await repository.mark_rewards_event_retry(
                    event,
                    now=datetime.now(UTC),
                    next_attempt_at=datetime.now(UTC) + timedelta(seconds=delay),
                    error=str(exc),
                )
                logger.exception("rewards event delivery failed event_id=%s", event.event_id)
                continue
            await repository.mark_rewards_event_delivered(event, now=datetime.now(UTC))
            delivered += 1
        await session.commit()
        return delivered


async def rewards_events_loop(redis: Redis | None = None) -> None:
    owned_redis = None
    target = redis
    if target is None:
        target = create_redis_pool(settings.diddi_rewards_events_redis_url or settings.redis_url)
        owned_redis = target
    try:
        while True:
            try:
                await asyncio.sleep(settings.diddi_rewards_events_delivery_interval_seconds)
                with worker_iteration("rewards-events"):
                    await run_rewards_events_once(target)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("rewards events delivery sweep failed")
    finally:
        if owned_redis is not None:
            with contextlib.suppress(Exception):
                await owned_redis.aclose()
