"""Redis-backed store for in-flight ride offers.

The matching engine offers a ride to one driver at a time (architecture doc
§7 step 3, API contract §4 `expires_in_seconds: 15`). Two facts must be
tracked between HTTP requests, and neither belongs in PostgreSQL — both are
short-lived and read on every driver action:

    rides:offer:{ride_id}          Redis set of drivers currently holding the
                                   active offer wave, with a TTL equal to the
                                   response window
    rides:offer:tried:{ride_id}    drivers already offered this ride, so a
                                   decline never loops back to them

The offer key's TTL *is* the timeout: if the driver does not answer, Redis
expires the key and the engine moves on. There is no timer to leak and no
scheduled job to miss.

Claiming is a `SET NX` — the first driver to accept wins and any concurrent
attempt fails, without a transaction or a lock.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from redis.asyncio import Redis

OFFER_KEY_PREFIX = "rides:offer:"
TRIED_KEY_PREFIX = "rides:offer:tried:"
CLAIM_KEY_PREFIX = "rides:claim:"

# How long a driver has to answer. The API contract advertises this to the
# driver app as `expires_in_seconds`.
OFFER_TTL_SECONDS = 15

# The tried-set outlives individual offers so a ride cycling through drivers
# never re-offers to someone who already declined.
TRIED_TTL_SECONDS = 900


@dataclass
class RedisOfferStore:
    redis: Redis
    offer_ttl_seconds: int = OFFER_TTL_SECONDS
    tried_ttl_seconds: int = TRIED_TTL_SECONDS

    async def open_offers(self, ride_id: UUID, driver_user_ids: list[UUID]) -> None:
        """Record the active offer wave for `ride_id`.

        Every driver in the wave is marked as tried immediately, so a later
        wave never loops back to them after decline or timeout.
        """
        if not driver_user_ids:
            return
        members = [str(driver_user_id) for driver_user_id in driver_user_ids]
        offer_key = f"{OFFER_KEY_PREFIX}{ride_id}"
        tried_key = f"{TRIED_KEY_PREFIX}{ride_id}"
        pipe = self.redis.pipeline()
        pipe.delete(offer_key)
        pipe.sadd(offer_key, *members)
        pipe.expire(offer_key, self.offer_ttl_seconds)
        pipe.sadd(tried_key, *members)
        pipe.expire(tried_key, self.tried_ttl_seconds)
        await pipe.execute()

    async def current_offers(self, ride_id: UUID) -> set[UUID]:
        """Drivers currently holding the active offer wave.

        Backward compatibility: older deployments stored this key as a single
        string value. If such a key still exists, read it as a one-driver wave.
        """
        key = f"{OFFER_KEY_PREFIX}{ride_id}"
        key_type = await self.redis.type(key)
        raw_type = key_type if isinstance(key_type, str) else key_type.decode()
        if raw_type == "none":
            return set()
        if raw_type == "string":
            value = await self.redis.get(key)
            return _uuid_set_from_raw_values([value])
        if raw_type == "set":
            return _uuid_set_from_raw_values(await self.redis.smembers(key))
        return set()

    async def close_offer(self, ride_id: UUID) -> None:
        """Withdraw the active offer wave (accepted, cancelled, or exhausted)."""
        await self.redis.delete(f"{OFFER_KEY_PREFIX}{ride_id}")

    async def decline_offer(self, ride_id: UUID, driver_user_id: UUID) -> bool:
        """Withdraw one driver from the active wave.

        Returns True when at least one other driver can still answer this same
        wave; False means the wave is exhausted and matching may advance.
        """
        key = f"{OFFER_KEY_PREFIX}{ride_id}"
        key_type = await self.redis.type(key)
        raw_type = key_type if isinstance(key_type, str) else key_type.decode()
        if raw_type == "set":
            await self.redis.srem(key, str(driver_user_id))
            remaining = await self.redis.scard(key)
            if not remaining:
                await self.redis.delete(key)
            return bool(remaining)
        if raw_type == "string":
            await self.redis.delete(key)
        return False

    async def already_tried(self, ride_id: UUID) -> set[UUID]:
        members = await self.redis.smembers(f"{TRIED_KEY_PREFIX}{ride_id}")
        tried: set[UUID] = set()
        for member in members or ():
            raw = member if isinstance(member, str) else member.decode()
            try:
                tried.add(UUID(raw))
            except ValueError:
                continue
        return tried

    async def claim(self, ride_id: UUID, driver_user_id: UUID) -> bool:
        """Atomically claim a ride for a driver.

        Returns True for the winner and False for everyone else. `SET NX` is
        what makes a double-accept race impossible: only one call can create
        the key, regardless of how many arrive at once.
        """
        won = await self.redis.set(
            f"{CLAIM_KEY_PREFIX}{ride_id}",
            str(driver_user_id),
            nx=True,
            ex=self.tried_ttl_seconds,
        )
        return bool(won)

    async def release_claim(self, ride_id: UUID) -> None:
        """Undo a claim — used when assignment fails after winning the race,
        so the ride can be offered onward instead of being stuck."""
        await self.redis.delete(f"{CLAIM_KEY_PREFIX}{ride_id}")

    async def clear(self, ride_id: UUID) -> None:
        """Drop all matching state for a ride (completed or cancelled)."""
        pipe = self.redis.pipeline()
        pipe.delete(f"{OFFER_KEY_PREFIX}{ride_id}")
        pipe.delete(f"{TRIED_KEY_PREFIX}{ride_id}")
        pipe.delete(f"{CLAIM_KEY_PREFIX}{ride_id}")
        await pipe.execute()


def _uuid_set_from_raw_values(values: object) -> set[UUID]:
    parsed: set[UUID] = set()
    for value in values or ():
        if value is None:
            continue
        raw = value if isinstance(value, str) else value.decode()
        try:
            parsed.add(UUID(raw))
        except ValueError:
            continue
    return parsed
