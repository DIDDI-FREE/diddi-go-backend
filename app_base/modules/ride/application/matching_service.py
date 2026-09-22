"""Ride matching engine.

Model: offer waves. A ride is offered to up to five nearby eligible drivers at
the same time. The first accept wins; declines remove one driver from the wave;
when the wave is exhausted or expires, matching advances to the next wave. If no
eligible candidate remains, the ride becomes `no_driver_found`.

Redis and the JWT both key drivers by auth user_id. `ride.rides.driver_id`
stores the local `ride.driver_profiles.id`, so the engine resolves user_id to
driver_profile before assigning a ride.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.payment.domain.interfaces import PaymentRepository
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
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
MAX_CANDIDATES = 25
OFFER_WAVE_SIZE = 5


@dataclass(frozen=True)
class MatchingDispatch:
    driver_user_ids: list[UUID]
    new_wave: bool
    no_driver_found: bool = False


@dataclass
class MatchingService:
    ride_repo: RideRepository
    driver_repo: DriverProfileRepository
    vehicle_repo: VehicleRepository
    locations: DriverLocationService
    offers: OfferStore
    partner_service: object | None = None
    payment_repo: PaymentRepository | None = None

    async def try_match(self, ride: Ride) -> MatchingDispatch:
        """Offer `ride` to the next suitable wave of drivers.

        Returns the driver auth user_ids holding the active wave. `new_wave`
        tells the presentation layer whether notifications must be sent.
        """
        logger.info(
            "matching_start ride_id=%s status=%s pickup_lat=%s pickup_lng=%s",
            ride.id,
            ride.status.value,
            ride.pickup_location.lat if ride.pickup_location else None,
            ride.pickup_location.lng if ride.pickup_location else None,
        )
        log_event(
            "ride.matching.started",
            ride_id=ride.id,
            status=ride.status.value,
            pickup={
                "lat": ride.pickup_location.lat if ride.pickup_location else None,
                "lng": ride.pickup_location.lng if ride.pickup_location else None,
            },
            vehicle_category=ride.vehicle_category.value,
            comfort_level=ride.comfort_level.value,
        )

        if ride.status != RideStatus.REQUESTED:
            logger.info("matching_skip ride_id=%s reason=status_not_requested status=%s", ride.id, ride.status.value)
            return MatchingDispatch([], new_wave=False)
        max_commission = Decimal(settings.driver_max_estimated_commission)
        if max_commission > 0 and ride.platform_commission is not None and ride.platform_commission > max_commission:
            logger.warning(
                "matching_skip ride_id=%s reason=estimated_commission_above_threshold commission=%s threshold=%s",
                ride.id,
                ride.platform_commission,
                max_commission,
            )
            log_event(
                "ride.matching.skipped",
                level="warning",
                ride_id=ride.id,
                reason="estimated_commission_above_threshold",
                platform_commission=ride.platform_commission,
                max_commission=max_commission,
            )
            await self._give_up(ride)
            return MatchingDispatch([], new_wave=True, no_driver_found=True)

        outstanding = await self.offers.current_offers(ride.id)
        if outstanding:
            logger.info(
                "matching_existing_offer_wave ride_id=%s driver_user_ids=%s",
                ride.id,
                [str(driver_user_id) for driver_user_id in outstanding],
            )
            log_event(
                "ride.matching.existing_offer_wave",
                ride_id=ride.id,
                driver_user_ids=[str(driver_user_id) for driver_user_id in outstanding],
                wave_size=len(outstanding),
            )
            return MatchingDispatch(list(outstanding), new_wave=False)

        candidates = await self._next_candidates(ride)
        if not candidates:
            await self._give_up(ride)
            return MatchingDispatch([], new_wave=True, no_driver_found=True)

        await self.offers.open_offers(ride.id, candidates)
        logger.info(
            "matching_offer_wave_opened ride_id=%s driver_user_ids=%s wave_size=%s",
            ride.id,
            [str(candidate) for candidate in candidates],
            len(candidates),
        )
        log_event(
            "ride.matching.offer_wave_sent",
            ride_id=ride.id,
            driver_user_ids=[str(candidate) for candidate in candidates],
            wave_size=len(candidates),
        )
        return MatchingDispatch(candidates, new_wave=True)

    async def accept(self, ride_id: UUID, driver_user_id: UUID) -> Ride:
        """A driver accepts the ride they were offered."""
        ride = await self._load_active_ride(ride_id)

        holders = await self.offers.current_offers(ride_id)
        if not holders:
            logger.info(
                "matching_accept_rejected ride_id=%s driver_user_id=%s reason=offer_expired",
                ride_id,
                driver_user_id,
            )
            log_event(
                "ride.matching.accept_rejected",
                ride_id=ride_id,
                driver_user_id=driver_user_id,
                reason="offer_expired",
            )
            raise ApiError(409, "OFFER_EXPIRED", "Cette demande n'est plus disponible.")
        if driver_user_id not in holders:
            logger.info(
                "matching_accept_rejected ride_id=%s driver_user_id=%s reason=offer_not_yours holders=%s",
                ride_id,
                driver_user_id,
                [str(holder) for holder in holders],
            )
            log_event(
                "ride.matching.accept_rejected",
                ride_id=ride_id,
                driver_user_id=driver_user_id,
                reason="offer_not_yours",
                holders=[str(holder) for holder in holders],
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
        except IntegrityError as exc:
            await self.offers.release_claim(ride_id)
            logger.warning(
                "matching_accept_rejected ride_id=%s driver_user_id=%s reason=driver_already_active",
                ride_id,
                driver_user_id,
            )
            log_event(
                "ride.matching.accept_rejected",
                level="warning",
                ride_id=ride_id,
                driver_user_id=driver_user_id,
                reason="driver_already_on_active_ride",
            )
            raise ApiError(
                409,
                ErrorCode.DRIVER_ALREADY_ON_ACTIVE_RIDE,
                "Ce chauffeur est deja affecte a une course active.",
            ) from exc
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
        log_event(
            "ride.accepted",
            ride_id=ride_id,
            driver_user_id=driver_user_id,
            driver_id=profile.id,
            vehicle_id=vehicle.id,
        )
        return ride

    async def decline(self, ride_id: UUID, driver_user_id: UUID) -> MatchingDispatch:
        """A driver declines.

        If other drivers still hold the same wave, matching does not advance.
        If the wave is exhausted, matching opens the next wave.
        """
        ride = await self._load_active_ride(ride_id)

        holders = await self.offers.current_offers(ride_id)
        if holders and driver_user_id not in holders:
            logger.info(
                "matching_decline_rejected ride_id=%s driver_user_id=%s reason=offer_not_yours holders=%s",
                ride_id,
                driver_user_id,
                [str(holder) for holder in holders],
            )
            raise ApiError(403, "OFFER_NOT_YOURS", "Cette demande a ete proposee a un autre chauffeur.")

        wave_still_active = await self.offers.decline_offer(ride_id, driver_user_id)
        logger.info(
            "matching_decline ride_id=%s driver_user_id=%s wave_still_active=%s",
            ride_id,
            driver_user_id,
            wave_still_active,
        )
        if wave_still_active:
            remaining = await self.offers.current_offers(ride_id)
            return MatchingDispatch(list(remaining), new_wave=False)
        return await self.try_match(ride)

    async def advance_expired_offer(self, ride_id: UUID) -> MatchingDispatch:
        """Advance matching after the active offer wave TTL has elapsed.

        The caller schedules this after `OFFER_TTL_SECONDS`. If any offer still
        exists, the wave is still active and no action is needed. If the ride has
        already been accepted/cancelled, no action is needed either.
        """
        outstanding = await self.offers.current_offers(ride_id)
        if outstanding:
            logger.info(
                "matching_expiry_skip ride_id=%s reason=offer_still_active wave_size=%s",
                ride_id,
                len(outstanding),
            )
            return MatchingDispatch(list(outstanding), new_wave=False)
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None or ride.status != RideStatus.REQUESTED:
            logger.info(
                "matching_expiry_skip ride_id=%s reason=ride_not_requested status=%s",
                ride_id,
                ride.status.value if ride else None,
            )
            return MatchingDispatch([], new_wave=False)
        logger.info("matching_expiry_advance ride_id=%s", ride_id)
        log_event("ride.matching.offer_wave_expired", ride_id=ride_id)
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

    async def _next_candidates(self, ride: Ride) -> list[UUID]:
        if ride.pickup_location is None:
            logger.info("matching_no_candidate ride_id=%s reason=no_pickup_location", ride.id)
            return []

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
        log_event(
            "ride.matching.candidates_found",
            ride_id=ride.id,
            candidates_count=len(nearby),
            radius_km=SEARCH_RADIUS_KM,
        )
        if not nearby:
            logger.info("matching_no_candidate ride_id=%s reason=no_available_nearby", ride.id)
            return []

        tried = await self.offers.already_tried(ride.id)
        selected: list[UUID] = []
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
                selected.append(user_id)
                if len(selected) >= OFFER_WAVE_SIZE:
                    break
                continue

            logger.info(
                "matching_candidate_rejected ride_id=%s driver_user_id=%s reason=%s",
                ride.id,
                user_id,
                reason,
            )
            log_event(
                "ride.matching.driver_filtered",
                ride_id=ride.id,
                driver_user_id=user_id,
                reason=reason,
            )

        if not selected:
            logger.info("matching_no_candidate ride_id=%s reason=all_candidates_rejected", ride.id)
        log_event(
            "ride.matching.driver_candidates_selected",
            ride_id=ride.id,
            driver_user_ids=[str(driver_user_id) for driver_user_id in selected],
            wave_size=len(selected),
        )
        return selected

    async def _can_take_ride(self, user_id: UUID, ride: Ride) -> tuple[bool, str | None]:
        profile = await self.driver_repo.find_by_user_id(user_id)
        if profile is None:
            return False, "driver_profile_not_found"
        if profile.status != DriverStatus.ACTIVE:
            return False, f"driver_profile_not_active:{profile.status.value}"
        vehicle = await self.vehicle_repo.find_active_for_driver(profile.id)
        if vehicle is None:
            return False, "no_active_vehicle"
        if self.partner_service is not None and hasattr(self.partner_service, "driver_is_blocked_by_partner"):
            blocked, partner_reason = await self.partner_service.driver_is_blocked_by_partner(profile.id)
            if blocked:
                return False, partner_reason or "partner_not_active"
        if self.payment_repo is not None:
            wallet = await self.payment_repo.get_or_create_wallet(profile.id)
            min_balance = Decimal(settings.driver_min_balance)
            if wallet.balance < min_balance:
                return False, f"driver_balance_too_low:{wallet.balance}<{min_balance}"
        if vehicle.category != ride.vehicle_category:
            return False, f"vehicle_category_mismatch:{vehicle.category.value}!={ride.vehicle_category.value}"
        if not _comfort_can_serve(vehicle.comfort_level, ride.comfort_level):
            return False, f"comfort_level_mismatch:{vehicle.comfort_level.value}<{ride.comfort_level.value}"
        return True, None

    async def _give_up(self, ride: Ride) -> None:
        ride.transition(RideStatus.NO_DRIVER_FOUND, when=datetime.now(UTC))
        await self.ride_repo.save(ride)
        for transition in ride.status_history:
            await self.ride_repo.record_status_transition(transition)
        await self.offers.clear(ride.id)
        logger.info("matching_no_driver_found ride_id=%s", ride.id)
        log_event("ride.matching.no_driver_found", ride_id=ride.id)

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


def _comfort_can_serve(vehicle_comfort: ComfortLevel, requested_comfort: ComfortLevel) -> bool:
    rank = {
        ComfortLevel.STANDARD: 1,
        ComfortLevel.COMFORT: 2,
        ComfortLevel.PREMIUM: 3,
    }
    return rank[vehicle_comfort] >= rank[requested_comfort]
