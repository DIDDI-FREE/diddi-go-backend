"""Ride matching engine — architecture doc §7 step 3.

Model: **sequential offers**. The ride is offered to the nearest available
driver, who has `OFFER_TTL_SECONDS` to answer. On decline or timeout it
passes to the next-nearest, and so on until someone accepts or the candidate
pool is exhausted — at which point the ride becomes `no_driver_found`.

Sequential rather than broadcast because it matches the contract's
`expires_in_seconds: 15` per-driver window, and because it guarantees a ride
is only ever promised to one driver at a time.

The 15-second window is enforced by the TTL on the Redis offer key rather
than by a background timer: whenever anything touches the ride (the driver
answers, the passenger polls, a later match attempt runs) the engine asks
Redis whether an offer is still outstanding. An expired key means the window
lapsed and the next driver can be offered. Nothing is scheduled, so nothing
is lost if the process restarts.

Identity note: Redis and the JWT both key drivers by `auth.users.id`, while
`ride.rides.driver_id` is a FK to `ride.driver_profiles.id`. The engine
resolves one to the other via `DriverProfileRepository.find_by_user_id`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app_base.core.errors import ApiError
from app_base.modules.ride.domain.entities import (
    DriverStatus,
    Ride,
    RideStatus,
)
from app_base.modules.ride.domain.interfaces import (
    DriverLocationService,
    DriverProfileRepository,
    OfferStore,
    RideRepository,
    VehicleRepository,
)

logger = logging.getLogger(__name__)

# How far to look for a driver. Abidjan-scale: beyond this the pickup ETA is
# long enough that the passenger is better served by no match than a match.
SEARCH_RADIUS_KM = 5.0

# Ceiling on how many drivers one ride is offered to before giving up.
MAX_CANDIDATES = 10


@dataclass
class MatchingService:
    ride_repo: RideRepository
    driver_repo: DriverProfileRepository
    vehicle_repo: VehicleRepository
    locations: DriverLocationService
    offers: OfferStore

    async def try_match(self, ride: Ride) -> UUID | None:
        """Offer `ride` to the next suitable driver.

        Returns the `user_id` of the driver now holding the offer, or None if
        nobody could be offered (in which case the ride is moved to
        `no_driver_found`).

        Safe to call repeatedly: if an offer is already outstanding and has
        not expired, it is left alone and the current holder is returned.
        """
        if ride.status != RideStatus.REQUESTED:
            return None

        outstanding = await self.offers.current_offer(ride.id)
        if outstanding is not None:
            return outstanding

        candidate = await self._next_candidate(ride)
        if candidate is None:
            await self._give_up(ride)
            return None

        await self.offers.open_offer(ride.id, candidate)
        logger.info("Ride %s offered to driver user_id=%s", ride.id, candidate)
        return candidate

    async def accept(self, ride_id: UUID, driver_user_id: UUID) -> Ride:
        """A driver accepts the ride they were offered.

        Raises if the offer is not theirs, has expired, or another driver has
        already claimed it.
        """
        ride = await self._load_active_ride(ride_id)

        holder = await self.offers.current_offer(ride_id)
        if holder is None:
            raise ApiError(
                409, "OFFER_EXPIRED", "Cette demande n'est plus disponible.",
            )
        if holder != driver_user_id:
            raise ApiError(
                403, "OFFER_NOT_YOURS", "Cette demande a été proposée à un autre chauffeur.",
            )

        # Resolve the driver before claiming so a driver who cannot actually
        # take the ride does not consume the claim.
        profile = await self.driver_repo.find_by_user_id(driver_user_id)
        if profile is None or profile.status != DriverStatus.ACTIVE:
            raise ApiError(
                403, "DRIVER_NOT_VERIFIED", "Votre profil chauffeur n'est pas validé.",
            )
        vehicle = await self.vehicle_repo.find_active_for_driver(profile.id)
        if vehicle is None:
            raise ApiError(
                409, "NO_ACTIVE_VEHICLE", "Aucun véhicule actif n'est associé à ce chauffeur.",
            )

        # Atomic: exactly one driver can win, even under simultaneous accepts.
        if not await self.offers.claim(ride_id, driver_user_id):
            raise ApiError(
                409, "RIDE_ALREADY_MATCHED", "Cette course a déjà été acceptée.",
            )

        try:
            ride.driver_id = profile.id
            ride.vehicle_id = vehicle.id
            ride.transition(RideStatus.MATCHED, when=datetime.now(UTC))
            await self.ride_repo.save(ride)
            for transition in ride.status_history:
                await self.ride_repo.record_status_transition(transition)
        except Exception:
            # Assignment failed after winning the race — release the claim so
            # the ride can still go to somebody else.
            await self.offers.release_claim(ride_id)
            raise

        await self.offers.close_offer(ride_id)
        # Out of the pool until this ride ends.
        await self.locations.set_available(driver_user_id, available=False)
        logger.info("Ride %s accepted by driver %s (profile %s)", ride_id, driver_user_id, profile.id)
        return ride

    async def decline(self, ride_id: UUID, driver_user_id: UUID) -> UUID | None:
        """A driver declines. The offer moves on to the next candidate.

        Returns the next driver offered, or None if the pool is exhausted.
        """
        ride = await self._load_active_ride(ride_id)

        holder = await self.offers.current_offer(ride_id)
        if holder is not None and holder != driver_user_id:
            raise ApiError(
                403, "OFFER_NOT_YOURS", "Cette demande a été proposée à un autre chauffeur.",
            )

        # Withdraw immediately so `try_match` looks for someone new. The
        # decliner stays in the tried-set, so they will not be re-offered.
        await self.offers.close_offer(ride_id)
        logger.info("Ride %s declined by driver user_id=%s", ride_id, driver_user_id)
        return await self.try_match(ride)

    async def release_driver(self, ride: Ride) -> None:
        """Return a driver to the pool once their ride ends (completed or
        cancelled) and drop the ride's matching state."""
        await self.offers.clear(ride.id)
        if ride.driver_id is None:
            return
        profile = await self.driver_repo.find_by_id(ride.driver_id)
        if profile is not None:
            await self.locations.set_available(profile.user_id, available=True)

    # -- internals ----------------------------------------------------------

    async def _next_candidate(self, ride: Ride) -> UUID | None:
        """Nearest available driver who has not already been offered this ride
        and can legally take it."""
        if ride.pickup_location is None:
            return None

        nearby = await self.locations.find_available_nearby(
            ride.pickup_location, radius_km=SEARCH_RADIUS_KM, limit=MAX_CANDIDATES,
        )
        if not nearby:
            return None

        tried = await self.offers.already_tried(ride.id)
        for user_id in nearby:
            if user_id in tried:
                continue
            if await self._can_take_ride(user_id):
                return user_id
        return None

    async def _can_take_ride(self, user_id: UUID) -> bool:
        """A driver in the Redis pool may still be unusable — suspended since
        going online, or without an active vehicle. Verify before offering."""
        profile = await self.driver_repo.find_by_user_id(user_id)
        if profile is None or profile.status != DriverStatus.ACTIVE:
            return False
        return await self.vehicle_repo.find_active_for_driver(profile.id) is not None

    async def _give_up(self, ride: Ride) -> None:
        """No candidate left: the passenger is told rather than left waiting."""
        ride.transition(RideStatus.NO_DRIVER_FOUND, when=datetime.now(UTC))
        await self.ride_repo.save(ride)
        for transition in ride.status_history:
            await self.ride_repo.record_status_transition(transition)
        await self.offers.clear(ride.id)
        logger.info("Ride %s found no driver", ride.id)

    async def _load_active_ride(self, ride_id: UUID) -> Ride:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Aucune course trouvée avec cet identifiant.")
        if ride.status == RideStatus.MATCHED:
            raise ApiError(409, "RIDE_ALREADY_MATCHED", "Cette course a déjà été acceptée.")
        if ride.status != RideStatus.REQUESTED:
            raise ApiError(
                409,
                "RIDE_NOT_OFFERABLE",
                "Cette course n'attend plus de chauffeur.",
                {"current_status": ride.status.value},
            )
        return ride
