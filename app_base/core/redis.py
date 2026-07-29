"""Redis client factory + FastAPI dependency.

A single `redis.asyncio.Redis` instance is shared across the app via
`app.state.redis`. The lifespan (see `app_base.core.lifespan`) creates it on
startup and closes it on shutdown. Routes consume it via `get_redis`.
"""

import logging

from redis.asyncio import Redis
from starlette.requests import Request

from app_base.core.settings import settings

# NOTE: no `from __future__ import annotations` here. FastAPI resolves the
# `Request` parameter of `get_redis` from its runtime annotation; with PEP 563
# postponed evaluation it sees the string "Request", fails to recognise it as
# the ASGI request, and treats it as a required query parameter — every route
# depending on it then 422s with `missing query.request`.

logger = logging.getLogger(__name__)


def create_redis_pool(url: str) -> Redis:
    """Construct the shared Redis async client.

    `decode_responses=True` means redis-py returns `str` / `list` of `str`
    instead of `bytes`, which removes boilerplate everywhere in the service
    layer at the cost of a negligible encode/decode overhead.
    """
    return Redis.from_url(url, decode_responses=True)


async def get_redis(request: Request) -> Redis:
    """FastAPI dependency — returns the shared pool from app state."""
    pool = getattr(request.app.state, "redis", None)
    if pool is None:
        # Defensive: if a test or one-off code path calls this without the
        # lifespan having run, build a throwaway client.
        pool = create_redis_pool(settings.redis_url)
    return pool
