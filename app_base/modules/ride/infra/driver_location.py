"""Redis GEO-backed driver location and availability service.

Architecture doc §2: a driver's position changes several times per minute —
too hot for PostgreSQL. Redis holds the *current* position of every active
driver; PostgreSQL keeps the sampled history (`ride.ride_route_points`) for
audit. DiddiMap does not cover proximity search, so this stays in-house.

Keys (all members are the driver's **auth user_id**, which is what the JWT
and the WebSocket carry — `driver_profiles.id` is resolved separately by the
matching engine):

    drivers:positions        GEO set — current position of every known driver
    drivers:seen:{id}        TTL marker — driver is connected and pushing
    drivers:available:{id}   TTL marker — driver is idle and wants a ride

Presence and availability are deliberately separate. A driver mid-ride is
still *present* (their position streams to the passenger) but not *available*
(they must not be offered another ride). `find_available_nearby` requires
both markers; `find_nearby` requires only presence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from redis.asyncio import Redis

from app_base.shared_kernel.types import GeoPoint

# Uvicorn wires this logger to the Docker console.
logger = logging.getLogger("uvicorn.error")

POSITIONS_KEY = "drivers:positions"
SEEN_KEY_PREFIX = "drivers:seen:"
AVAILABLE_KEY_PREFIX = "drivers:available:"

# A driver who hasn't pushed a position in this long is treated as gone.
# The API contract asks the driver app to push every 3–5s, so 30s tolerates
# a dozen missed beats on a bad connection before dropping them.
PRESENCE_TTL_SECONDS = 30

# Availability outlives a few missed heartbeats: a driver waiting at a rank
# with a flaky connection should not silently leave the matching pool. Their
# presence marker expiring is what removes them.
AVAILABILITY_TTL_SECONDS = 300


@dataclass
class RedisDriverLocationService:
    redis: Redis
    presence_ttl_seconds: int = PRESENCE_TTL_SECONDS
    availability_ttl_seconds: int = AVAILABILITY_TTL_SECONDS

    async def update_position(self, driver_id: UUID, location: GeoPoint) -> None:
        """Record a driver's current position and refresh their presence marker.

        Called on every `driver.location_push` WebSocket frame, so it must stay
        cheap: one GEOADD + one SET, pipelined into a single round trip.

        This refreshes presence but never availability — a driver on a ride
        keeps streaming position without re-entering the matching pool.
        """
        member = str(driver_id)
        pipe = self.redis.pipeline()
        # GEOADD takes longitude first.
        pipe.geoadd(POSITIONS_KEY, (location.lng, location.lat, member))
        pipe.set(f"{SEEN_KEY_PREFIX}{member}", "1", ex=self.presence_ttl_seconds)
        await pipe.execute()
        logger.info(
            "driver_position_updated user_id=%s lat=%s lng=%s presence_ttl_seconds=%s",
            driver_id,
            location.lat,
            location.lng,
            self.presence_ttl_seconds,
        )

    async def set_available(self, driver_id: UUID, *, available: bool) -> None:
        """Add or remove a driver from the pool of candidates for new rides.

        Set False when a ride is accepted, True again when it completes or is
        cancelled. Idempotent in both directions.
        """
        key = f"{AVAILABLE_KEY_PREFIX}{driver_id}"
        if available:
            await self.redis.set(key, "1", ex=self.availability_ttl_seconds)
            logger.info(
                "driver_available_set user_id=%s available=true availability_ttl_seconds=%s",
                driver_id,
                self.availability_ttl_seconds,
            )
        else:
            await self.redis.delete(key)
            logger.info("driver_available_set user_id=%s available=false", driver_id)

    async def is_available(self, driver_id: UUID) -> bool:
        return bool(await self.redis.exists(f"{AVAILABLE_KEY_PREFIX}{driver_id}"))

    async def find_nearby(
        self,
        location: GeoPoint,
        radius_km: float,
        limit: int = 20,
    ) -> list[UUID]:
        """Driver IDs within `radius_km`, nearest first, excluding drivers
        whose presence marker has expired. Does not filter on availability."""
        return await self._search(location, radius_km, limit, require_available=False)

    async def find_available_nearby(
        self,
        location: GeoPoint,
        radius_km: float,
        limit: int = 20,
    ) -> list[UUID]:
        """Candidates for matching: present, idle, nearest first."""
        return await self._search(location, radius_km, limit, require_available=True)

    async def _search(
        self,
        location: GeoPoint,
        radius_km: float,
        limit: int,
        *,
        require_available: bool,
    ) -> list[UUID]:
        # Over-fetch when filtering: GEOSEARCH's COUNT is applied before we
        # can drop busy drivers, so a small limit could otherwise come back
        # empty while idle drivers sit just outside the truncated window.
        fetch = limit * 4 if require_available else limit
        candidates = await self.redis.geosearch(
            POSITIONS_KEY,
            longitude=location.lng,
            latitude=location.lat,
            radius=radius_km,
            unit="km",
            sort="ASC",
            count=fetch,
        )
        if not candidates:
            logger.info(
                "driver_geo_search_empty lat=%s lng=%s radius_km=%s limit=%s require_available=%s",
                location.lat,
                location.lng,
                radius_km,
                limit,
                require_available,
            )
            return []

        members = [c if isinstance(c, str) else c.decode() for c in candidates]
        pipe = self.redis.pipeline()
        for member in members:
            pipe.exists(f"{SEEN_KEY_PREFIX}{member}")
            if require_available:
                pipe.exists(f"{AVAILABLE_KEY_PREFIX}{member}")
        flags = await pipe.execute()
        logger.info(
            "driver_geo_search_raw lat=%s lng=%s radius_km=%s limit=%s require_available=%s members=%s flags=%s",
            location.lat,
            location.lng,
            radius_km,
            limit,
            require_available,
            members,
            [bool(flag) for flag in flags],
        )

        stride = 2 if require_available else 1
        nearby: list[UUID] = []
        for index, member in enumerate(members):
            window = flags[index * stride : (index + 1) * stride]
            if not all(window):
                logger.info(
                    "driver_geo_candidate_rejected user_id=%s reason=%s",
                    member,
                    _missing_marker_reason(window, require_available=require_available),
                )
                continue
            try:
                nearby.append(UUID(member))
            except ValueError:
                logger.warning("Ignoring non-UUID member in %s: %r", POSITIONS_KEY, member)
            if len(nearby) >= limit:
                break
        logger.info(
            "driver_geo_search_result lat=%s lng=%s radius_km=%s count=%s candidates=%s",
            location.lat,
            location.lng,
            radius_km,
            len(nearby),
            [str(driver_id) for driver_id in nearby],
        )
        return nearby

    async def get_position(self, driver_id: UUID) -> GeoPoint | None:
        """Current position of one driver, or None if unknown."""
        positions = await self.redis.geopos(POSITIONS_KEY, str(driver_id))
        if not positions or positions[0] is None:
            return None
        lng, lat = positions[0]
        return GeoPoint(lat=float(lat), lng=float(lng))

    async def go_offline(self, driver_id: UUID) -> None:
        """Drop a driver from matching immediately (app closed, shift ended).

        The GEO member is removed alongside both markers so a stale position
        can't linger in proximity results.
        """
        member = str(driver_id)
        pipe = self.redis.pipeline()
        pipe.zrem(POSITIONS_KEY, member)
        pipe.delete(f"{SEEN_KEY_PREFIX}{member}")
        pipe.delete(f"{AVAILABLE_KEY_PREFIX}{member}")
        await pipe.execute()
        logger.info("driver_offline user_id=%s", driver_id)


def _missing_marker_reason(window: list[int], *, require_available: bool) -> str:
    if not window or not bool(window[0]):
        return "presence_expired"
    if require_available and len(window) > 1 and not bool(window[1]):
        return "not_available"
    return "unknown_marker_state"
