"""Ride use cases — DB-backed, stateless, injected repositories.

Driver assignment is not handled here: `MatchingService`
(`ride/application/matching_service.py`) owns the offer loop and the
`requested → matched` transition. This service covers pricing, creation,
reads, the driver-driven status transitions after matching, cancellation,
and ratings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app_base.core.errors import ApiError
from app_base.modules.auth.domain.interfaces import UserRepository
from app_base.modules.ride.domain.entities import (
    VALID_CANCEL_REASONS,
    CancelReason,
    InvalidStatusTransition,
    Ride,
    RideRating,
    RideStatus,
    VehicleCategory,
)
from app_base.modules.ride.domain.interfaces import (
    DriverProfileRepository,
    PricingRuleRepository,
    RideRepository,
    VehicleRepository,
)
from app_base.shared_kernel.contracts.routing import RoutingProvider
from app_base.shared_kernel.types import GeoPoint

# Default formula (XOF) — used only when no pricing rule has been seeded for
# the city/category. Geographic data must still come from DiddiMap.
_DEFAULT_BASE_FARE = Decimal("250")
_DEFAULT_PRICE_PER_KM = Decimal("240")


def iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class RideService:
    ride_repo: RideRepository
    routing: RoutingProvider
    pricing_rules: PricingRuleRepository
    # Optional so pricing-only and unit-test wiring stays light. When present,
    # ride detail responses can resolve the assigned driver and vehicle.
    driver_repo: DriverProfileRepository | None = None
    vehicle_repo: VehicleRepository | None = None
    user_repo: UserRepository | None = None

    async def estimate_pricing(
        self,
        pickup: GeoPoint,
        dropoff: GeoPoint,
        vehicle_category: str,
    ) -> dict:
        if vehicle_category not in {"standard", "comfort", "van"}:
            raise ApiError(422, "INVALID_VEHICLE_CATEGORY", "Catégorie de véhicule invalide.")
        category = VehicleCategory(vehicle_category)

        # DiddiMap is the single source of geographic truth. Pricing remains
        # DiddiGo-owned, but distance/duration must come from DiddiMap.
        estimate = await self.routing.estimate(origin=pickup, destination=dropoff, profile="palh_vtc")
        distance_km = _coerce_decimal(estimate.distance_km)
        duration_seconds = int(estimate.duration_seconds)
        if distance_km <= 0:
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Distance DiddiMap invalide.")

        # 2) Apply pricing rule if seeded — otherwise default formula.
        rule = await self.pricing_rules.find_active(city="Abidjan", vehicle_category=category)
        if rule is None:
            base_fare = _DEFAULT_BASE_FARE
            price_per_km = _DEFAULT_PRICE_PER_KM
            surge_multiplier = Decimal("1.0")
        else:
            base_fare = rule.base_fare
            price_per_km = rule.price_per_km
            surge_multiplier = rule.surge_multiplier

        estimated_fare = int(round(float((base_fare + distance_km * price_per_km) * surge_multiplier)))
        return {
            "estimated_fare": estimated_fare,
            "currency": "XOF",
            "distance_km": float(distance_km),
            "duration_seconds": duration_seconds,
            "surge_multiplier": float(surge_multiplier),
        }

    async def request_ride(
        self,
        *,
        passenger_user_id: UUID,
        pickup: GeoPoint,
        pickup_address: str | None,
        dropoff: GeoPoint,
        dropoff_address: str | None,
        vehicle_category: str,
        scheduled_at: datetime | None,
    ) -> Ride:
        """Persist a new ride in `requested`.

        Returns the entity rather than a response payload so the caller can
        hand it straight to the matching engine; the router renders it with
        `ride_creation_payload`.
        """
        if vehicle_category not in {"standard", "comfort", "van"}:
            raise ApiError(422, "INVALID_VEHICLE_CATEGORY", "Catégorie de véhicule invalide.")
        if await self.ride_repo.has_active_ride(passenger_user_id):
            raise ApiError(
                409,
                "ACTIVE_RIDE_ALREADY_EXISTS",
                "Un passager ne peut pas avoir deux courses actives simultanément.",
            )

        pricing = await self.estimate_pricing(pickup, dropoff, vehicle_category)
        ride = Ride(
            id=Ride.new_id(),
            passenger_user_id=passenger_user_id,
            status=RideStatus.REQUESTED,
            vehicle_category=VehicleCategory(vehicle_category),
            pickup_location=pickup,
            pickup_address=pickup_address,
            dropoff_location=dropoff,
            dropoff_address=dropoff_address,
            scheduled_at=scheduled_at,
            estimated_fare=Decimal(pricing["estimated_fare"]),
            currency="XOF",
            distance_km=Decimal(str(pricing["distance_km"])),
            duration_seconds=pricing["duration_seconds"],
            requested_at=datetime.utcnow(),
        )
        await self.ride_repo.save(ride)
        for transition in ride.status_history:
            await self.ride_repo.record_status_transition(transition)
        return ride

    async def load_ride(self, ride_id: UUID) -> Ride:
        """Fetch the entity without access control — for callers that have
        already authorised the actor (e.g. the matching flow re-reading a ride
        to build a WebSocket payload)."""
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Aucune course trouvée avec cet identifiant.")
        return ride

    async def get_ride(self, ride_id: UUID, *, actor_user_id: UUID, actor_role: str) -> dict:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Aucune course trouvée avec cet identifiant.")
        if ride.passenger_user_id != actor_user_id and actor_role != "driver" and actor_role != "admin":
            raise ApiError(403, "RIDE_NOT_OWNED_BY_USER", "Cette course ne vous appartient pas.")
        driver = await self._driver_payload(ride)
        return _ride_detail_payload(ride, driver=driver)

    async def _driver_payload(self, ride: Ride) -> dict | None:
        """Driver + vehicle block for a ride detail response.

        Null until a driver is assigned, per the API contract §2: "`driver` est
        `null` tant que `status = "requested"` ou `"no_driver_found"`".
        """
        if ride.driver_id is None or self.driver_repo is None:
            return None
        profile = await self.driver_repo.find_by_id(ride.driver_id)
        if profile is None:
            return None

        vehicle = None
        if self.vehicle_repo is not None:
            vehicle = await self.vehicle_repo.find_active_for_driver(profile.id)

        full_name = None
        phone = None
        if self.user_repo is not None:
            # Cross-module read through the auth module's repository port —
            # never a JOIN into `auth.users` from ride SQL.
            user = await self.user_repo.find_by_id(profile.user_id)
            if user is not None:
                full_name = user.full_name
                phone = user.phone

        return {
            "id": str(profile.id),
            "full_name": full_name,
            "rating_avg": float(profile.rating_avg) if profile.rating_avg is not None else None,
            "phone": phone,
            "vehicle": {
                "make": vehicle.make,
                "model": vehicle.model,
                "color": vehicle.color,
                "plate_number": vehicle.plate_number,
            } if vehicle else None,
        }

    async def list_rides(
        self,
        *,
        actor_user_id: UUID,
        actor_role: str,
        passenger_user_id: UUID | None = None,
        driver_id: UUID | None = None,
        status: RideStatus | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        # Default filter: scope to the caller's rides. Admins can pass a
        # different passenger_user_id / driver_id to browse.
        if actor_role not in {"admin", "driver"}:
            passenger_user_id = actor_user_id
            driver_id = None
        rides, total = await self.ride_repo.list_by(
            passenger_user_id=passenger_user_id,
            driver_id=driver_id,
            status=status,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        return {
            "data": [_ride_summary_payload(r) for r in rides],
            "pagination": {"page": page, "page_size": page_size, "total_items": total, "total_pages": total_pages},
        }

    async def update_status(
        self,
        ride_id: UUID,
        new_status: RideStatus,
        *,
        actor_user_id: UUID,
    ) -> dict:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Aucune course trouvée avec cet identifiant.")
        try:
            ride.transition(new_status)
        except InvalidStatusTransition as exc:
            raise ApiError(
                409,
                "INVALID_STATUS_TRANSITION",
                "Transition de statut invalide.",
                {"current_status": ride.status.value, "attempted_status": new_status.value},
            ) from exc
        await self.ride_repo.save(ride)
        # `transition()` appends exactly one entry; the entity was loaded fresh
        # from the repository so anything already in `status_history` came from
        # this call. Persist all of it.
        for transition in ride.status_history:
            await self.ride_repo.record_status_transition(transition)
        return _ride_detail_payload(ride, driver=None)

    async def cancel(self, ride_id: UUID, reason: str, *, actor_role: str) -> dict:
        if reason not in VALID_CANCEL_REASONS:
            raise ApiError(422, "INVALID_CANCEL_REASON", "Motif d'annulation invalide.")
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Aucune course trouvée avec cet identifiant.")
        if ride.status == RideStatus.COMPLETED:
            raise ApiError(409, "RIDE_ALREADY_COMPLETED", "La course est déjà terminée.")
        if ride.status in {RideStatus.CANCELLED_BY_PASSENGER, RideStatus.CANCELLED_BY_DRIVER}:
            raise ApiError(409, "RIDE_ALREADY_CANCELLED", "La course est déjà annulée.")
        if ride.status == RideStatus.NO_DRIVER_FOUND:
            # Terminal already — there is nothing left to cancel. Without this
            # the transition below raises and surfaces as a 500.
            raise ApiError(
                409, "RIDE_NOT_CANCELLABLE", "Cette course n'a pas trouvé de chauffeur.",
            )
        new_status = (
            RideStatus.CANCELLED_BY_DRIVER if reason == CancelReason.DRIVER_UNAVAILABLE.value or actor_role == "driver"
            else RideStatus.CANCELLED_BY_PASSENGER
        )
        ride.transition(new_status, metadata={"reason": reason})
        ride.cancellation_reason = reason
        await self.ride_repo.save(ride)
        return {
            "id": str(ride.id),
            "status": ride.status.value,
            "cancelled_at": iso_utc(ride.cancelled_at),
        }

    async def rate(
        self,
        ride_id: UUID,
        rating: int,
        comment: str | None,
        *,
        actor_role: str,
    ) -> dict:
        if actor_role not in {"passenger", "driver"}:
            raise ApiError(403, "FORBIDDEN", "Seul passager ou chauffeur peut noter une course.")
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Aucune course trouvée avec cet identifiant.")
        if await self.ride_repo.has_rated(ride_id, actor_role):
            raise ApiError(409, "RATING_ALREADY_SUBMITTED", "La notation a déjà été envoyée pour ce rôle.")
        if not 1 <= rating <= 5:
            raise ApiError(422, "RATING_OUT_OF_RANGE", "La note doit être comprise entre 1 et 5.")
        rating_entity = RideRating(
            id=Ride.new_id(),
            ride_id=ride_id,
            rater_role=actor_role,
            rating=rating,
            comment=comment,
        )
        await self.ride_repo.save_rating(rating_entity)
        return {"id": str(rating_entity.id), "ride_id": str(ride_id), "rating": rating}


# ---------------------------------------------------------------------------
# Payloads (private)
# ---------------------------------------------------------------------------

def ride_creation_payload(ride: Ride) -> dict:
    return {
        "ride_id": str(ride.id),
        "status": ride.status.value,
        "estimated_fare": int(ride.estimated_fare) if ride.estimated_fare is not None else None,
        "currency": ride.currency,
        "requested_at": iso_utc(ride.requested_at),
    }


def _ride_summary_payload(ride: Ride) -> dict:
    return {
        "id": str(ride.id),
        "status": ride.status.value,
        "final_fare": int(ride.final_fare) if ride.final_fare is not None else None,
        "completed_at": iso_utc(ride.completed_at),
        "pickup_address": ride.pickup_address,
        "dropoff_address": ride.dropoff_address,
    }


def _ride_detail_payload(ride: Ride, driver: dict | None) -> dict:
    return {
        "id": str(ride.id),
        "status": ride.status.value,
        # `full_name` needs a cross-module read through the auth module's
        # application layer; wired in a later iteration.
        "passenger": {"id": str(ride.passenger_user_id), "full_name": None},
        "driver": driver,
        "pickup": {
            "lat": ride.pickup_location.lat if ride.pickup_location else None,
            "lng": ride.pickup_location.lng if ride.pickup_location else None,
            "address": ride.pickup_address,
        },
        "dropoff": {
            "lat": ride.dropoff_location.lat if ride.dropoff_location else None,
            "lng": ride.dropoff_location.lng if ride.dropoff_location else None,
            "address": ride.dropoff_address,
        },
        "estimated_fare": int(ride.estimated_fare) if ride.estimated_fare is not None else None,
        "final_fare": int(ride.final_fare) if ride.final_fare is not None else None,
        "currency": ride.currency,
        "distance_km": float(ride.distance_km) if ride.distance_km is not None else None,
        "duration_seconds": ride.duration_seconds,
        "requested_at": iso_utc(ride.requested_at),
        "matched_at": iso_utc(ride.matched_at),
        "started_at": iso_utc(ride.started_at),
        "completed_at": iso_utc(ride.completed_at),
    }


def _coerce_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, int):
        return Decimal(value)
    return Decimal("0")
