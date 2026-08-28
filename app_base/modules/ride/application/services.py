"""Ride use cases - DB-backed, stateless, injected repositories."""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app_base.core.errors import ApiError
from app_base.modules.auth.domain.interfaces import UserRepository
from app_base.modules.ride.domain.entities import (
    VALID_CANCEL_REASONS,
    CancelReason,
    ComfortLevel,
    InvalidStatusTransition,
    PaymentMethod,
    Ride,
    RideRating,
    RideRoutePoint,
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

logger = logging.getLogger("uvicorn.error")

_DEFAULT_BASE_FARE = Decimal("250")
_DEFAULT_PRICE_PER_KM = Decimal("240")
_DEFAULT_PRICE_PER_MIN = Decimal("0")
_SURGE_CAP = Decimal("1.60")
_COMMISSION_RATE = Decimal("0.08")
_SHARE_TOKEN_BYTES = 24
_SHARE_TTL_HOURS = 24


def iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class RideService:
    ride_repo: RideRepository
    routing: RoutingProvider
    pricing_rules: PricingRuleRepository
    driver_repo: DriverProfileRepository | None = None
    vehicle_repo: VehicleRepository | None = None
    user_repo: UserRepository | None = None

    async def estimate_pricing(
        self,
        pickup: GeoPoint,
        dropoff: GeoPoint,
        vehicle_category: str,
        comfort_level: str = "standard",
    ) -> dict:
        category = _vehicle_category(vehicle_category)
        comfort = _comfort_level(comfort_level)

        estimate = await self.routing.estimate(origin=pickup, destination=dropoff, profile="palh_vtc")
        distance_km = _coerce_decimal(estimate.distance_km)
        duration_seconds = int(estimate.duration_seconds)
        if distance_km <= 0:
            raise ApiError(502, "DIDDIMAP_INVALID_RESPONSE", "Distance DiddiMap invalide.")

        rule = await self.pricing_rules.find_active(city="Abidjan", vehicle_category=category)
        base_fare = rule.base_fare if rule else _DEFAULT_BASE_FARE
        price_per_km = rule.price_per_km if rule else _DEFAULT_PRICE_PER_KM
        price_per_min = rule.price_per_min if rule else _DEFAULT_PRICE_PER_MIN
        surge_multiplier = min(rule.surge_multiplier if rule else Decimal("1.00"), _SURGE_CAP)
        pricing = _pricing_breakdown(
            distance_km=distance_km,
            duration_seconds=duration_seconds,
            base_fare=base_fare,
            price_per_km=price_per_km,
            price_per_min=price_per_min,
            surge_multiplier=surge_multiplier,
            comfort_multiplier=_comfort_multiplier(comfort),
        )
        return _pricing_response(distance_km, duration_seconds, pricing, surge_multiplier, comfort)

    async def request_ride(
        self,
        *,
        passenger_user_id: UUID,
        pickup: GeoPoint,
        pickup_address: str | None,
        dropoff: GeoPoint,
        dropoff_address: str | None,
        vehicle_category: str,
        comfort_level: str,
        payment_method: str,
        scheduled_at: datetime | None,
    ) -> Ride:
        category = _vehicle_category(vehicle_category)
        comfort = _comfort_level(comfort_level)
        method = _payment_method(payment_method)
        if await self.ride_repo.has_active_ride(passenger_user_id):
            raise ApiError(
                409,
                "ACTIVE_RIDE_ALREADY_EXISTS",
                "Un passager ne peut pas avoir deux courses actives simultanement.",
            )

        pricing = await self.estimate_pricing(pickup, dropoff, vehicle_category, comfort_level)
        ride = Ride(
            id=Ride.new_id(),
            passenger_user_id=passenger_user_id,
            status=RideStatus.REQUESTED,
            vehicle_category=category,
            comfort_level=comfort,
            pickup_location=pickup,
            pickup_address=pickup_address,
            dropoff_location=dropoff,
            dropoff_address=dropoff_address,
            scheduled_at=scheduled_at,
            estimated_fare=Decimal(pricing["estimated_fare"]),
            currency="XOF",
            distance_km=Decimal(str(pricing["distance_km"])),
            duration_seconds=pricing["duration_seconds"],
            base_fare=Decimal(pricing["base_fare"]),
            distance_fare=Decimal(pricing["distance_fare"]),
            duration_fare=Decimal(pricing["duration_fare"]),
            surge_multiplier=Decimal(str(pricing["surge_multiplier"])),
            surge_cap=Decimal(str(pricing["surge_cap"])),
            commission_rate=Decimal(str(pricing["commission_rate"])),
            platform_commission=Decimal(pricing["platform_commission"]),
            driver_payout_estimate=Decimal(pricing["driver_payout_estimate"]),
            payment_method=method,
            requested_at=datetime.utcnow(),
        )
        await self.ride_repo.save(ride)
        for transition in ride.status_history:
            await self.ride_repo.record_status_transition(transition)
        return ride

    async def load_ride(self, ride_id: UUID) -> Ride:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Aucune course trouvee avec cet identifiant.")
        return ride

    async def get_ride(self, ride_id: UUID, *, actor_user_id: UUID, actor_role: str) -> dict:
        ride = await self.load_ride(ride_id)
        is_admin = actor_role == "admin"
        is_passenger = ride.passenger_user_id == actor_user_id
        is_assigned_driver = await self._is_assigned_driver(ride, actor_user_id)
        if not is_passenger and not is_assigned_driver and not is_admin:
            logger.warning(
                "ride_detail_denied ride_id=%s actor_user_id=%s actor_role=%s passenger_user_id=%s driver_id=%s",
                ride_id,
                actor_user_id,
                actor_role,
                ride.passenger_user_id,
                ride.driver_id,
            )
            raise ApiError(403, "RIDE_NOT_OWNED_BY_USER", "Cette course ne vous appartient pas.")
        return _ride_detail_payload(ride, driver=await self._driver_payload(ride))

    async def _driver_payload(self, ride: Ride) -> dict | None:
        if ride.driver_id is None or self.driver_repo is None:
            return None
        profile = await self.driver_repo.find_by_id(ride.driver_id)
        if profile is None:
            return None
        vehicle = await self.vehicle_repo.find_active_for_driver(profile.id) if self.vehicle_repo else None
        full_name = None
        phone = None
        if self.user_repo is not None:
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
                "category": vehicle.category.value,
                "comfort_level": vehicle.comfort_level.value,
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
        actor_role = _normalise_actor_role(actor_role)
        if actor_role == "driver" and driver_id is None:
            driver_id = await self._driver_profile_id_for_user(actor_user_id)
            if driver_id is None:
                return _paginated_rides([], 0, page=page, page_size=page_size)
        elif actor_role != "admin":
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
        return _paginated_rides(rides, total, page=page, page_size=page_size)

    async def update_status(self, ride_id: UUID, new_status: RideStatus, *, actor_user_id: UUID) -> dict:
        ride = await self.load_ride(ride_id)
        if new_status is RideStatus.COMPLETED:
            await self._apply_actual_pricing_if_possible(ride)
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
        for transition in ride.status_history:
            await self.ride_repo.record_status_transition(transition)
        return _ride_detail_payload(ride, driver=None)

    async def cancel(self, ride_id: UUID, reason: str, *, actor_user_id: UUID, actor_role: str) -> dict:
        if reason not in VALID_CANCEL_REASONS:
            raise ApiError(422, "INVALID_CANCEL_REASON", "Motif d'annulation invalide.")
        ride = await self.load_ride(ride_id)
        if ride.status == RideStatus.COMPLETED:
            raise ApiError(409, "RIDE_ALREADY_COMPLETED", "La course est deja terminee.")
        if ride.status in {RideStatus.CANCELLED_BY_PASSENGER, RideStatus.CANCELLED_BY_DRIVER}:
            raise ApiError(409, "RIDE_ALREADY_CANCELLED", "La course est deja annulee.")
        if ride.status == RideStatus.NO_DRIVER_FOUND:
            raise ApiError(409, "RIDE_NOT_CANCELLABLE", "Cette course n'a pas trouve de chauffeur.")
        is_driver = actor_role == "driver" or await self._is_assigned_driver(ride, actor_user_id)
        new_status = (
            RideStatus.CANCELLED_BY_DRIVER
            if reason == CancelReason.DRIVER_UNAVAILABLE.value or is_driver
            else RideStatus.CANCELLED_BY_PASSENGER
        )
        ride.transition(new_status, metadata={"reason": reason})
        ride.cancellation_reason = reason
        await self.ride_repo.save(ride)
        return {"id": str(ride.id), "status": ride.status.value, "cancelled_at": iso_utc(ride.cancelled_at)}

    async def rate(
        self,
        ride_id: UUID,
        rating: int,
        comment: str | None,
        *,
        actor_user_id: UUID,
        actor_role: str,
    ) -> dict:
        ride = await self.load_ride(ride_id)
        rater_role = await self._rating_role_for_actor(ride, actor_user_id, actor_role)
        if rater_role is None:
            raise ApiError(403, "RIDE_NOT_OWNED_BY_USER", "Cette course ne vous appartient pas.")
        if await self.ride_repo.has_rated(ride_id, rater_role):
            raise ApiError(409, "RATING_ALREADY_SUBMITTED", "La notation a deja ete envoyee pour ce role.")
        if not 1 <= rating <= 5:
            raise ApiError(422, "RATING_OUT_OF_RANGE", "La note doit etre comprise entre 1 et 5.")
        rating_entity = RideRating(
            id=Ride.new_id(),
            ride_id=ride_id,
            rater_role=rater_role,
            rating=rating,
            comment=comment,
        )
        await self.ride_repo.save_rating(rating_entity)
        return {"id": str(rating_entity.id), "ride_id": str(ride_id), "rating": rating, "rater_role": rater_role}

    async def add_location_samples(self, ride_id: UUID, samples: list[dict], *, actor_user_id: UUID) -> dict:
        ride = await self.load_ride(ride_id)
        if not await self._is_assigned_driver(ride, actor_user_id):
            raise ApiError(403, "RIDE_NOT_OWNED_BY_USER", "Seul le chauffeur assigne peut envoyer ces traces.")
        now = datetime.now(UTC)
        points = [
            RideRoutePoint(
                ride_id=ride_id,
                location=GeoPoint(lat=float(sample["lat"]), lng=float(sample["lng"])),
                recorded_at=sample.get("recorded_at") or now,
                heading=sample.get("heading"),
                speed_kmh=Decimal(str(sample["speed_kmh"])) if sample.get("speed_kmh") is not None else None,
                accuracy_m=Decimal(str(sample["accuracy_m"])) if sample.get("accuracy_m") is not None else None,
                source=sample.get("source", "driver"),
            )
            for sample in samples
        ]
        await self.ride_repo.save_route_points(points)
        return {"ride_id": str(ride_id), "accepted_samples": len(points)}

    async def create_share_link(self, ride_id: UUID, *, actor_user_id: UUID, actor_role: str) -> dict:
        ride = await self.load_ride(ride_id)
        is_participant = ride.passenger_user_id == actor_user_id or await self._is_assigned_driver(ride, actor_user_id)
        if not is_participant and actor_role != "admin":
            raise ApiError(403, "RIDE_NOT_OWNED_BY_USER", "Cette course ne vous appartient pas.")
        if not ride.share_token:
            ride.share_token = secrets.token_urlsafe(_SHARE_TOKEN_BYTES)
        ride.share_expires_at = datetime.now(UTC) + timedelta(hours=_SHARE_TTL_HOURS)
        await self.ride_repo.save(ride)
        return {
            "ride_id": str(ride.id),
            "share_token": ride.share_token,
            "expires_at": iso_utc(ride.share_expires_at),
            "public_path": f"/v1/rides/shared/{ride.share_token}",
        }

    async def get_shared_ride(self, token: str) -> dict:
        ride = await self.ride_repo.find_by_share_token(token)
        if ride is None or ride.share_expires_at is None or ride.share_expires_at < datetime.now(UTC):
            raise ApiError(404, "SHARE_LINK_NOT_FOUND", "Lien de partage introuvable ou expire.")
        latest = await self.ride_repo.latest_route_point(ride.id)
        position = latest.location if latest else None
        return {
            "ride_id": str(ride.id),
            "status": ride.status.value,
            "driver_location": {"lat": position.lat, "lng": position.lng} if position else None,
            "last_location_at": iso_utc(latest.recorded_at) if latest else None,
            "pickup": _point_payload(ride.pickup_location, ride.pickup_address),
            "dropoff": _point_payload(ride.dropoff_location, ride.dropoff_address),
        }

    async def request_emergency(
        self,
        ride_id: UUID,
        *,
        actor_user_id: UUID,
        actor_role: str,
        note: str | None,
    ) -> dict:
        ride = await self.load_ride(ride_id)
        is_participant = ride.passenger_user_id == actor_user_id or await self._is_assigned_driver(ride, actor_user_id)
        if not is_participant and actor_role != "admin":
            raise ApiError(403, "RIDE_NOT_OWNED_BY_USER", "Cette course ne vous appartient pas.")
        ride.emergency_requested_at = datetime.now(UTC)
        ride.emergency_status = "open"
        ride.emergency_note = note
        await self.ride_repo.save(ride)
        logger.warning("ride_emergency ride_id=%s actor_user_id=%s actor_role=%s", ride_id, actor_user_id, actor_role)
        return {"ride_id": str(ride.id), "status": "open", "requested_at": iso_utc(ride.emergency_requested_at)}

    async def _driver_profile_id_for_user(self, user_id: UUID) -> UUID | None:
        if self.driver_repo is None:
            return None
        profile = await self.driver_repo.find_by_user_id(user_id)
        return profile.id if profile is not None else None

    async def _is_assigned_driver(self, ride: Ride, user_id: UUID) -> bool:
        if ride.driver_id is None:
            return False
        return ride.driver_id == await self._driver_profile_id_for_user(user_id)

    async def _rating_role_for_actor(self, ride: Ride, user_id: UUID, token_role: str) -> str | None:
        if ride.passenger_user_id == user_id:
            return "passenger"
        if token_role == "admin":
            return None
        if await self._is_assigned_driver(ride, user_id):
            return "driver"
        return None

    async def _apply_actual_pricing_if_possible(self, ride: Ride) -> None:
        # V3 records real GPS samples. Until Map Core exposes a route-match REST
        # contract, final fare keeps the DiddiMap estimate but stores the actual
        # fields only after an explicit provider-backed calculation. Do not copy
        # the estimate into "actual" fields: that would be a silent fallback.
        latest = await self.ride_repo.latest_route_point(ride.id)
        if latest is None:
            return
        logger.info(
            "ride_actual_pricing_pending ride_id=%s reason=diddimap_map_matching_rest_contract_missing",
            ride.id,
        )


def ride_creation_payload(ride: Ride) -> dict:
    return {
        "ride_id": str(ride.id),
        "status": ride.status.value,
        "estimated_fare": int(ride.estimated_fare) if ride.estimated_fare is not None else None,
        "currency": ride.currency,
        "payment_method": ride.payment_method.value,
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


def _paginated_rides(rides: list[Ride], total: int, *, page: int, page_size: int) -> dict:
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "data": [_ride_summary_payload(r) for r in rides],
        "pagination": {"page": page, "page_size": page_size, "total_items": total, "total_pages": total_pages},
    }


def _normalise_actor_role(role: str) -> str:
    return "passenger" if role in {"user", "passenger"} else role


def _ride_detail_payload(ride: Ride, driver: dict | None) -> dict:
    return {
        "id": str(ride.id),
        "status": ride.status.value,
        "passenger": {"id": str(ride.passenger_user_id), "full_name": None},
        "driver": driver,
        "pickup": _point_payload(ride.pickup_location, ride.pickup_address),
        "dropoff": _point_payload(ride.dropoff_location, ride.dropoff_address),
        "vehicle_category": ride.vehicle_category.value,
        "comfort_level": ride.comfort_level.value,
        "estimated_fare": int(ride.estimated_fare) if ride.estimated_fare is not None else None,
        "final_fare": int(ride.final_fare) if ride.final_fare is not None else None,
        "currency": ride.currency,
        "distance_km": float(ride.distance_km) if ride.distance_km is not None else None,
        "duration_seconds": ride.duration_seconds,
        "pricing": {
            "base_fare": int(ride.base_fare) if ride.base_fare is not None else None,
            "distance_fare": int(ride.distance_fare) if ride.distance_fare is not None else None,
            "duration_fare": int(ride.duration_fare) if ride.duration_fare is not None else None,
            "surge_multiplier": float(ride.surge_multiplier),
            "surge_cap": float(ride.surge_cap),
            "commission_rate": float(ride.commission_rate),
            "comfort_multiplier": float(_comfort_multiplier(ride.comfort_level)),
            "platform_commission": int(ride.platform_commission) if ride.platform_commission is not None else None,
            "driver_payout_estimate": int(ride.driver_payout_estimate)
            if ride.driver_payout_estimate is not None
            else None,
            "actual_distance_km": float(ride.actual_distance_km) if ride.actual_distance_km is not None else None,
            "actual_duration_seconds": ride.actual_duration_seconds,
        },
        "payment": {
            "method": ride.payment_method.value,
            "transaction_id": str(ride.payment_transaction_id) if ride.payment_transaction_id else None,
        },
        "emergency": {
            "status": ride.emergency_status,
            "requested_at": iso_utc(ride.emergency_requested_at),
        },
        "requested_at": iso_utc(ride.requested_at),
        "matched_at": iso_utc(ride.matched_at),
        "started_at": iso_utc(ride.started_at),
        "completed_at": iso_utc(ride.completed_at),
    }


def _point_payload(point: GeoPoint | None, address: str | None) -> dict:
    return {
        "lat": point.lat if point else None,
        "lng": point.lng if point else None,
        "address": address,
    }


def _pricing_breakdown(
    *,
    distance_km: Decimal,
    duration_seconds: int,
    base_fare: Decimal,
    price_per_km: Decimal,
    price_per_min: Decimal,
    surge_multiplier: Decimal,
    comfort_multiplier: Decimal,
) -> dict[str, Decimal]:
    duration_minutes = Decimal(duration_seconds) / Decimal(60)
    distance_fare = distance_km * price_per_km
    duration_fare = duration_minutes * price_per_min
    total_fare = (base_fare + distance_fare + duration_fare) * comfort_multiplier * surge_multiplier
    rounded_total = Decimal(round(float(total_fare)))
    platform_commission = Decimal(round(float(rounded_total * _COMMISSION_RATE)))
    return {
        "base_fare": base_fare,
        "distance_fare": Decimal(round(float(distance_fare))),
        "duration_fare": Decimal(round(float(duration_fare))),
        "total_fare": rounded_total,
        "platform_commission": platform_commission,
        "driver_payout_estimate": rounded_total - platform_commission,
    }


def _pricing_response(
    distance_km: Decimal,
    duration_seconds: int,
    pricing: dict[str, Decimal],
    surge_multiplier: Decimal,
    comfort: ComfortLevel,
) -> dict:
    return {
        "estimated_fare": int(pricing["total_fare"]),
        "currency": "XOF",
        "distance_km": float(distance_km),
        "duration_seconds": duration_seconds,
        "surge_multiplier": float(surge_multiplier),
        "surge_cap": float(_SURGE_CAP),
        "comfort_multiplier": float(_comfort_multiplier(comfort)),
        "base_fare": int(pricing["base_fare"]),
        "distance_fare": int(pricing["distance_fare"]),
        "duration_fare": int(pricing["duration_fare"]),
        "commission_rate": float(_COMMISSION_RATE),
        "platform_commission": int(pricing["platform_commission"]),
        "driver_payout_estimate": int(pricing["driver_payout_estimate"]),
    }


def _vehicle_category(value: str) -> VehicleCategory:
    try:
        return VehicleCategory(value)
    except ValueError as exc:
        raise ApiError(422, "INVALID_VEHICLE_CATEGORY", "Categorie de vehicule invalide.") from exc


def _comfort_level(value: str) -> ComfortLevel:
    try:
        return ComfortLevel(value)
    except ValueError as exc:
        raise ApiError(422, "INVALID_COMFORT_LEVEL", "Niveau de confort invalide.") from exc


def _comfort_multiplier(value: ComfortLevel) -> Decimal:
    return {
        ComfortLevel.STANDARD: Decimal("1.00"),
        ComfortLevel.COMFORT: Decimal("1.15"),
        ComfortLevel.PREMIUM: Decimal("1.30"),
    }[value]


def _payment_method(value: str) -> PaymentMethod:
    try:
        return PaymentMethod(value)
    except ValueError as exc:
        raise ApiError(422, "INVALID_PAYMENT_METHOD", "Methode de paiement invalide.") from exc


def _coerce_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, int):
        return Decimal(value)
    return Decimal("0")
