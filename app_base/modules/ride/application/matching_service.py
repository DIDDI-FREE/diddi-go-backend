"""Ride matching engine.

Model: sequential offers. A ride is offered to the nearest available driver,
then to the next one on decline/timeout. If no eligible candidate remains, the
ride becomes `no_driver_found`.

Redis and the JWT both key drivers by auth user_id. `ride.rides.driver_id`
stores the local `ride.driver_profiles.id`, so the engine resolves user_id to
driver_profile before assigning a ride.
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

# Uvicorn wires this logger to the Docker console.
logger = logging.getLogger("uvicorn.error")

SEARCH_RADIUS_KM = 5.0
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

        Returns the driver auth user_id holding the offer, or None if the ride
        has moved to `no_driver_found`.
        """
        logger.info(
            "matching_start ride_id=%s status=%s pickup_lat=%s pickup_lng=%s",
            ride.id,
            ride.status.value,
            ride.pickup_location.lat if ride.pickup_location else None,
            ride.pickup_location.lng if ride.pickup_location else None,
        )

        if ride.status != RideStatus.REQUESTED:
            logger.info("matching_skip ride_id=%s reason=status_not_requested status=%s", ride.id, ride.status.value)
            return None

        outstanding = await self.offers.current_offer(ride.id)
        if outstanding is not None:
            logger.info("matching_existing_offer ride_id=%s driver_user_id=%s", ride.id, outstanding)
            return outstanding

        candidate = await self._next_candidate(ride)
        if candidate is None:
            await self._give_up(ride)
            return None

        await self.offers.open_offer(ride.id, candidate)
        logger.info("matching_offer_opened ride_id=%s driver_user_id=%s", ride.id, candidate)
        return candidate

    async def accept(self, ride_id: UUID, driver_user_id: UUID) -> Ride:
        """A driver accepts the ride they were offered."""
        ride = await self._load_active_ride(ride_id)

        holder = await self.offers.current_offer(ride_id)
        if holder is None:
            logger.info(
                "matching_accept_rejected ride_id=%s driver_user_id=%s reason=offer_expired",
                ride_id,
                driver_user_id,
            )
            raise ApiError(409, "OFFER_EXPIRED", "Cette demande n'est plus disponible.")
        if holder != driver_user_id:
            logger.info(
                "matching_accept_rejected ride_id=%s driver_user_id=%s reason=offer_not_yours holder=%s",
                ride_id,
                driver_user_id,
                holder,
            )
            raise ApiError(403, "OFFER_NOT_YOURS", "Cette demande a ete proposee a un autre chauffeur.")

        profile = await self.driver_repo.find_by_user_id(driver_user_id)
        if profile is None or profile.status != DriverStatus.ACTIVE:
            logger.info(
                "matching_accept_rejected ride_id=%s driver_user_id=%s reason=driver_not_verified profile_found=%s",
                ride_id,
                driver_user_id,
                profile is not None,
            )
            raise ApiError(403, "DRIVER_NOT_VERIFIED", "Votre profil chauffeur n'est pas valide.")

        vehicle = await self.vehicle_repo.find_active_for_driver(profile.id)
        if vehicle is None:
            logger.info(
                "matching_accept_rejected ride_id=%s driver_user_id=%s reason=no_active_vehicle profile_id=%s",
                ride_id,
                driver_user_id,
                profile.id,
            )
            raise ApiError(409, "NO_ACTIVE_VEHICLE", "Aucun vehicule actif n'est associe a ce chauffeur.")

        if not await self.offers.claim(ride_id, driver_user_id):
            logger.info(
                "matching_accept_rejected ride_id=%s driver_user_id=%s reason=already_claimed",
                ride_id,
                driver_user_id,
            )
            raise ApiError(409, "RIDE_ALREADY_MATCHED", "Cette course a deja ete acceptee.")

        try:
            ride.driver_id = profile.id
            ride.vehicle_id = vehicle.id
            ride.transition(RideStatus.MATCHED, when=datetime.now(UTC))
            await self.ride_repo.save(ride)
            for transition in ride.status_history:
                await self.ride_repo.record_status_transition(transition)
        except Exception:
            await self.offers.release_claim(ride_id)
            raise

        await self.offers.close_offer(ride_id)
        await self.locations.set_available(driver_user_id, available=False)
        logger.info(
            "matching_accept_success ride_id=%s driver_user_id=%s driver_profile_id=%s vehicle_id=%s",
            ride_id,
            driver_user_id,
            profile.id,
            vehicle.id,
        )
        return ride

    async def decline(self, ride_id: UUID, driver_user_id: UUID) -> UUID | None:
        """A driver declines. The offer moves on to the next candidate."""
        ride = await self._load_active_ride(ride_id)

        holder = await self.offers.current_offer(ride_id)
        if holder is not None and holder != driver_user_id:
            logger.info(
                "matching_decline_rejected ride_id=%s driver_user_id=%s reason=offer_not_yours holder=%s",
                ride_id,
                driver_user_id,
                holder,
            )
            raise ApiError(403, "OFFER_NOT_YOURS", "Cette demande a ete proposee a un autre chauffeur.")

        await self.offers.close_offer(ride_id)
        logger.info("matching_decline ride_id=%s driver_user_id=%s", ride_id, driver_user_id)
        return await self.try_match(ride)

    async def release_driver(self, ride: Ride) -> None:
        """Return a driver to the pool once their ride ends."""
        await self.offers.clear(ride.id)
        if ride.driver_id is None:
            logger.info("matching_release_driver ride_id=%s driver_profile_id=None", ride.id)
            return
        profile = await self.driver_repo.find_by_id(ride.driver_id)
        if profile is not None:
            await self.locations.set_available(profile.user_id, available=True)
            logger.info(
                "matching_release_driver ride_id=%s driver_profile_id=%s driver_user_id=%s",
                ride.id,
                ride.driver_id,
                profile.user_id,
            )

    async def _next_candidate(self, ride: Ride) -> UUID | None:
        if ride.pickup_location is None:
            logger.info("matching_no_candidate ride_id=%s reason=no_pickup_location", ride.id)
            return None

        nearby = await self.locations.find_available_nearby(
            ride.pickup_location,
            radius_km=SEARCH_RADIUS_KM,
            limit=MAX_CANDIDATES,
        )
        logger.info(
            "matching_nearby_candidates ride_id=%s count=%s candidates=%s",
            ride.id,
            len(nearby),
            [str(user_id) for user_id in nearby],
        )
        if not nearby:
            logger.info("matching_no_candidate ride_id=%s reason=no_available_nearby", ride.id)
            return None

        tried = await self.offers.already_tried(ride.id)
        for user_id in nearby:
            if user_id in tried:
                logger.info(
                    "matching_candidate_rejected ride_id=%s driver_user_id=%s reason=already_tried",
                    ride.id,
                    user_id,
                )
                continue

            can_take, reason = await self._can_take_ride(user_id, ride)
            if can_take:
                logger.info("matching_candidate_selected ride_id=%s driver_user_id=%s", ride.id, user_id)
                return user_id

            logger.info(
                "matching_candidate_rejected ride_id=%s driver_user_id=%s reason=%s",
                ride.id,
                user_id,
                reason,
            )

        logger.info("matching_no_candidate ride_id=%s reason=all_candidates_rejected", ride.id)
        return None

    async def _can_take_ride(self, user_id: UUID, ride: Ride) -> tuple[bool, str | None]:
        profile = await self.driver_repo.find_by_user_id(user_id)
        if profile is None:
            return False, "driver_profile_not_found"
        if profile.status != DriverStatus.ACTIVE:
            return False, f"driver_profile_not_active:{profile.status.value}"
        vehicle = await self.vehicle_repo.find_active_for_driver(profile.id)
        if vehicle is None:
            return False, "no_active_vehicle"
        if vehicle.category != ride.vehicle_category:
            return False, f"vehicle_category_mismatch:{vehicle.category.value}!={ride.vehicle_category.value}"
        if vehicle.comfort_level != ride.comfort_level:
            return False, f"comfort_level_mismatch:{vehicle.comfort_level.value}!={ride.comfort_level.value}"
        return True, None

    async def _give_up(self, ride: Ride) -> None:
        ride.transition(RideStatus.NO_DRIVER_FOUND, when=datetime.now(UTC))
        await self.ride_repo.save(ride)
        for transition in ride.status_history:
            await self.ride_repo.record_status_transition(transition)
        await self.offers.clear(ride.id)
        logger.info("matching_no_driver_found ride_id=%s", ride.id)

    async def _load_active_ride(self, ride_id: UUID) -> Ride:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Aucune course trouvee avec cet identifiant.")
        if ride.status == RideStatus.MATCHED:
            raise ApiError(409, "RIDE_ALREADY_MATCHED", "Cette course a deja ete acceptee.")
        if ride.status != RideStatus.REQUESTED:
            raise ApiError(
                409,
                "RIDE_NOT_OFFERABLE",
                "Cette course n'attend plus de chauffeur.",
                {"current_status": ride.status.value},
            )
        return ride
