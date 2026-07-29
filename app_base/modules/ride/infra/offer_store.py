"""Redis-backed store for in-flight ride offers.

The matching engine offers a ride to one driver at a time (architecture doc
§7 step 3, API contract §4 `expires_in_seconds: 15`). Two facts must be
tracked between HTTP requests, and neither belongs in PostgreSQL — both are
short-lived and read on every driver action:

    rides:offer:{ride_id}          which driver currently holds the offer,
                                   with a TTL equal to the response window
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

    async def open_offer(self, ride_id: UUID, driver_user_id: UUID) -> None:
        """Record that `driver_user_id` now holds the offer for `ride_id`,
        and mark them as tried so they are not offered it again."""
        pipe = self.redis.pipeline()
        pipe.set(
            f"{OFFER_KEY_PREFIX}{ride_id}",
            str(driver_user_id),
            ex=self.offer_ttl_seconds,
        )
        pipe.sadd(f"{TRIED_KEY_PREFIX}{ride_id}", str(driver_user_id))
        pipe.expire(f"{TRIED_KEY_PREFIX}{ride_id}", self.tried_ttl_seconds)
        await pipe.execute()

    async def current_offer(self, ride_id: UUID) -> UUID | None:
        """Driver currently holding the offer, or None if nobody does —
        either it was never opened, it was answered, or it expired."""
        value = await self.redis.get(f"{OFFER_KEY_PREFIX}{ride_id}")
        if value is None:
            return None
        raw = value if isinstance(value, str) else value.decode()
        try:
            return UUID(raw)
        except ValueError:
            return None

    async def close_offer(self, ride_id: UUID) -> None:
        """Withdraw the outstanding offer (declined, accepted, or cancelled)."""
        await self.redis.delete(f"{OFFER_KEY_PREFIX}{ride_id}")

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
