"""Redis cache for immutable or short-lived Pilotage breakdown snapshots."""

import json
from datetime import datetime
from decimal import Decimal

from redis.asyncio import Redis

from app_base.modules.ride.domain.breakdown import BreakdownItem, RideBreakdown

CACHE_VERSION = "v1"


class RedisRideBreakdownCache:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    @staticmethod
    def key(day: str, dimension: str, metric: str) -> str:
        return f"pilotage:breakdown:{CACHE_VERSION}:{day}:{dimension}:{metric}"

    async def get(self, day: str, dimension: str, metric: str) -> RideBreakdown | None:
        payload = await self._redis.get(self.key(day, dimension, metric))
        if payload is None:
            return None
        data = json.loads(payload)
        return RideBreakdown(
            total=Decimal(data["total"]),
            items=tuple(
                BreakdownItem(key=item["key"], value=Decimal(item["value"]))
                for item in data["items"]
            ),
            calculated_at=datetime.fromisoformat(data["calculated_at"].replace("Z", "+00:00")),
        )

    async def set(
        self,
        day: str,
        dimension: str,
        metric: str,
        breakdown: RideBreakdown,
        *,
        ttl_seconds: int,
    ) -> None:
        payload = json.dumps(
            {
                "total": str(breakdown.total),
                "items": [{"key": item.key, "value": str(item.value)} for item in breakdown.items],
                "calculated_at": breakdown.calculated_at.isoformat().replace("+00:00", "Z"),
            },
            separators=(",", ":"),
        )
        await self._redis.set(self.key(day, dimension, metric), payload, ex=ttl_seconds)

