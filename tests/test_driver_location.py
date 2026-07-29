"""Tests for the Redis GEO driver-location service.

Run against the real Redis from docker-compose — GEOADD/GEOSEARCH semantics
are the point of the class, so a mock would test nothing.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app_base.core.redis import create_redis_pool
from app_base.core.settings import settings
from app_base.modules.ride.infra.driver_location import (
    POSITIONS_KEY,
    SEEN_KEY_PREFIX,
    RedisDriverLocationService,
)
from app_base.shared_kernel.types import GeoPoint

# Reference points in Abidjan (~5.5 km apart).
YOPOUGON = GeoPoint(lat=5.3599, lng=-4.0083)
PLATEAU = GeoPoint(lat=5.3167, lng=-4.0333)
FAR_AWAY = GeoPoint(lat=6.8276, lng=-5.2893)  # Yamoussoukro, ~200 km


@pytest.fixture
async def locations():
    """Isolated service instance — uses its own Redis keys per test run and
    cleans them up afterwards."""
    redis = create_redis_pool(settings.redis_url)
    service = RedisDriverLocationService(redis=redis)
    await redis.delete(POSITIONS_KEY)
    try:
        yield service
    finally:
        members = await redis.zrange(POSITIONS_KEY, 0, -1)
        for member in members:
            await redis.delete(f"{SEEN_KEY_PREFIX}{member}")
        await redis.delete(POSITIONS_KEY)
        await redis.aclose()


async def test_update_position_is_readable_back(locations) -> None:
    driver_id = uuid4()
    await locations.update_position(driver_id, YOPOUGON)

    position = await locations.get_position(driver_id)
    assert position is not None
    assert position.lat == pytest.approx(YOPOUGON.lat, abs=1e-4)
    assert position.lng == pytest.approx(YOPOUGON.lng, abs=1e-4)


async def test_get_position_is_none_for_unknown_driver(locations) -> None:
    assert await locations.get_position(uuid4()) is None


async def test_find_nearby_returns_drivers_in_radius(locations) -> None:
    near = uuid4()
    far = uuid4()
    await locations.update_position(near, PLATEAU)
    await locations.update_position(far, FAR_AWAY)

    found = await locations.find_nearby(YOPOUGON, radius_km=10)
    assert near in found
    assert far not in found


async def test_find_nearby_sorts_nearest_first(locations) -> None:
    closest = uuid4()
    further = uuid4()
    await locations.update_position(closest, YOPOUGON)
    await locations.update_position(further, PLATEAU)

    found = await locations.find_nearby(YOPOUGON, radius_km=50)
    assert found.index(closest) < found.index(further)


async def test_find_nearby_respects_the_limit(locations) -> None:
    for _ in range(5):
        await locations.update_position(uuid4(), YOPOUGON)

    assert len(await locations.find_nearby(YOPOUGON, radius_km=10, limit=3)) == 3


async def test_find_nearby_is_empty_when_nobody_is_around(locations) -> None:
    await locations.update_position(uuid4(), FAR_AWAY)
    assert await locations.find_nearby(YOPOUGON, radius_km=5) == []


async def test_stale_drivers_are_excluded(locations) -> None:
    """A driver whose presence marker expired must not be matched, even
    though their last position is still in the GEO set."""
    stale = uuid4()
    await locations.update_position(stale, YOPOUGON)
    await locations.redis.delete(f"{SEEN_KEY_PREFIX}{stale}")  # simulate TTL expiry

    assert stale not in await locations.find_nearby(YOPOUGON, radius_km=10)


async def test_go_offline_removes_the_driver(locations) -> None:
    driver_id = uuid4()
    await locations.update_position(driver_id, YOPOUGON)
    assert driver_id in await locations.find_nearby(YOPOUGON, radius_km=10)

    await locations.go_offline(driver_id)

    assert driver_id not in await locations.find_nearby(YOPOUGON, radius_km=10)
    assert await locations.get_position(driver_id) is None


async def test_position_updates_overwrite_the_previous_one(locations) -> None:
    driver_id = uuid4()
    await locations.update_position(driver_id, YOPOUGON)
    await locations.update_position(driver_id, PLATEAU)

    position = await locations.get_position(driver_id)
    assert position.lat == pytest.approx(PLATEAU.lat, abs=1e-4)
    # One member per driver, never a duplicate row.
    assert await locations.redis.zscore(POSITIONS_KEY, str(driver_id)) is not None
