"""Ride domain interfaces — repository + service protocols.

Clean architecture rule: these protocols define WHAT the ride module needs
from its data / external layers, regardless of HOW. The SQLAlchemy-backed
implementations in `ride/infra/repositories.py` + `ride/infra/driver_location.py`
satisfy them today; tomorrow a Redis/DiddiMap swap or a DiddiPay migration
happens by changing the `infra/` without touching `application/` or `domain/`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app_base.modules.ride.domain.entities import (
    DriverProfile,
    DriverStatus,
    PricingRule,
    Ride,
    RideRating,
    RideRoutePoint,
    RideStatus,
    RideStatusTransition,
    Vehicle,
    VehicleCategory,
)
from app_base.shared_kernel.types import GeoPoint


class RideRepository(Protocol):
    async def save(self, ride: Ride) -> Ride: ...

    async def find_by_id(self, ride_id: UUID) -> Ride | None: ...

    async def find_by_share_token(self, token: str) -> Ride | None: ...

    async def list_by(
        self,
        *,
        passenger_user_id: UUID | None = None,
        driver_id: UUID | None = None,
        status: RideStatus | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Ride], int]:
        """Return a page of rides + the total item count for pagination."""
        ...

    async def has_active_ride(self, passenger_user_id: UUID) -> bool:
        """A passenger cannot have two rides in active states simultaneously.
        Active = {requested, matched, driver_en_route, in_progress}."""
        ...

    async def record_status_transition(self, transition: RideStatusTransition) -> None: ...

    async def save_rating(self, rating: RideRating) -> RideRating: ...

    async def has_rated(self, ride_id: UUID, rater_role: str) -> bool: ...

    async def save_route_points(self, points: list[RideRoutePoint]) -> None: ...

    async def latest_route_point(self, ride_id: UUID) -> RideRoutePoint | None: ...

    async def list_route_points(self, ride_id: UUID) -> list[RideRoutePoint]: ...


class DriverProfileRepository(Protocol):
    async def save(self, profile: DriverProfile) -> DriverProfile: ...

    async def find_by_user_id(self, user_id: UUID) -> DriverProfile | None: ...

    async def find_by_id(self, profile_id: UUID) -> DriverProfile | None: ...

    async def list_by_status(
        self,
        statuses: list[DriverStatus],
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DriverProfile], int]:
        """Return driver KYC/admin review queue entries + total count."""
        ...


class VehicleRepository(Protocol):
    async def find_active_for_driver(self, driver_id: UUID) -> Vehicle | None: ...

    async def save(self, vehicle: Vehicle) -> Vehicle: ...


class PricingRuleRepository(Protocol):
    async def find_active(
        self,
        city: str,
        vehicle_category: VehicleCategory,
        as_of: datetime | None = None,
    ) -> PricingRule | None:
        """Returns the single pricing rule in force for this city / category
        at time `as_of` (defaults to now). None if no rule has been seeded yet."""
        ...


class DriverLocationService(Protocol):
    """Redis GEO-backed port for live driver position and availability.

    Members are the driver's **auth user_id** (what the JWT and WebSocket
    carry), not `driver_profiles.id`.
    """

    async def update_position(self, driver_id: UUID, location: GeoPoint) -> None: ...

    async def set_available(self, driver_id: UUID, *, available: bool) -> None:
        """Add to / remove from the pool of candidates for new rides."""
        ...

    async def is_available(self, driver_id: UUID) -> bool: ...

    async def find_nearby(
        self, location: GeoPoint, radius_km: float, limit: int = 20,
    ) -> list[UUID]:
        """Driver IDs sorted nearest-first, filtered on presence only."""
        ...

    async def find_available_nearby(
        self, location: GeoPoint, radius_km: float, limit: int = 20,
    ) -> list[UUID]:
        """Matching candidates: present, idle, nearest first."""
        ...

    async def get_position(self, driver_id: UUID) -> GeoPoint | None: ...

    async def go_offline(self, driver_id: UUID) -> None: ...


class OfferStore(Protocol):
    """Short-lived state for in-flight ride offers.

    Implemented against Redis (`ride/infra/offer_store.py`) because every
    entry is transient and TTL-driven: the offer key's expiry *is* the
    driver's response window.
    """

    async def open_offer(self, ride_id: UUID, driver_user_id: UUID) -> None:
        """Record the offer holder and mark them tried."""
        ...

    async def current_offer(self, ride_id: UUID) -> UUID | None:
        """Holder of the outstanding offer, or None if none/expired/answered."""
        ...

    async def close_offer(self, ride_id: UUID) -> None: ...

    async def already_tried(self, ride_id: UUID) -> set[UUID]:
        """Drivers this ride has been offered to, so none is asked twice."""
        ...

    async def claim(self, ride_id: UUID, driver_user_id: UUID) -> bool:
        """Atomically claim the ride. True for exactly one caller."""
        ...

    async def release_claim(self, ride_id: UUID) -> None: ...

    async def clear(self, ride_id: UUID) -> None: ...
