"""Ride domain entities — plain dataclasses, no SQLAlchemy dependency.

Clean architecture rule: the domain entity owns the business rules
(the state machine, the cancellation semantics). Services orchestrate
by calling the entity, not by re-implementing the validation inline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from app_base.shared_kernel.types import GeoPoint


class RideStatus(str, Enum):
    REQUESTED = "requested"
    MATCHED = "matched"
    DRIVER_EN_ROUTE = "driver_en_route"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED_BY_PASSENGER = "cancelled_by_passenger"
    CANCELLED_BY_DRIVER = "cancelled_by_driver"
    NO_DRIVER_FOUND = "no_driver_found"


# Transitions allowed from each status — architecture doc §4 state machine.
ALLOWED_TRANSITIONS: dict[RideStatus, set[RideStatus]] = {
    RideStatus.REQUESTED: {
        RideStatus.MATCHED,
        RideStatus.NO_DRIVER_FOUND,
        RideStatus.CANCELLED_BY_PASSENGER,
        RideStatus.CANCELLED_BY_DRIVER,
    },
    RideStatus.MATCHED: {
        RideStatus.DRIVER_EN_ROUTE,
        RideStatus.CANCELLED_BY_PASSENGER,
        RideStatus.CANCELLED_BY_DRIVER,
    },
    RideStatus.DRIVER_EN_ROUTE: {
        RideStatus.IN_PROGRESS,
        RideStatus.CANCELLED_BY_PASSENGER,
        RideStatus.CANCELLED_BY_DRIVER,
    },
    RideStatus.IN_PROGRESS: {
        RideStatus.COMPLETED,
        RideStatus.CANCELLED_BY_PASSENGER,
        RideStatus.CANCELLED_BY_DRIVER,
    },
    # Terminal states — no further transitions allowed.
    RideStatus.COMPLETED: set(),
    RideStatus.CANCELLED_BY_PASSENGER: set(),
    RideStatus.CANCELLED_BY_DRIVER: set(),
    RideStatus.NO_DRIVER_FOUND: set(),
}


class VehicleCategory(str, Enum):
    STANDARD = "standard"
    COMFORT = "comfort"
    VAN = "van"


class ComfortLevel(str, Enum):
    STANDARD = "standard"
    COMFORT = "comfort"
    PREMIUM = "premium"


class PaymentMethod(str, Enum):
    CASH = "cash"
    WAVE = "wave"
    DIDDIPAY = "diddipay"


class DriverStatus(str, Enum):
    """Lifecycle of a driver's account (architecture doc §3.2).

    `offline` is a KYC/account state, not a real-time presence signal —
    whether a driver is currently reachable lives in Redis, not here.
    """

    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    OFFLINE = "offline"


class CancelReason(str, Enum):
    PASSENGER_CHANGED_MIND = "passenger_changed_mind"
    PASSENGER_NO_SHOW = "passenger_no_show"
    DRIVER_UNAVAILABLE = "driver_unavailable"
    FOUND_ALTERNATIVE = "found_alternative"
    OTHER = "other"


VALID_CANCEL_REASONS = {r.value for r in CancelReason}


class InvalidStatusTransition(Exception):
    """Raised by `Ride.transition` when the caller attempts a move not in
    `ALLOWED_TRANSITIONS`. Surfaces as `409 INVALID_STATUS_TRANSITION` at
    the API boundary."""


@dataclass
class Ride:
    """Core entity for a ride request."""

    id: UUID
    passenger_user_id: UUID
    status: RideStatus = RideStatus.REQUESTED
    vehicle_category: VehicleCategory = VehicleCategory.STANDARD
    comfort_level: ComfortLevel = ComfortLevel.STANDARD

    pickup_location: GeoPoint | None = None
    pickup_address: str | None = None
    dropoff_location: GeoPoint | None = None
    dropoff_address: str | None = None

    scheduled_at: datetime | None = None
    requested_at: datetime | None = None
    matched_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None

    # Pricing
    estimated_fare: Decimal | None = None
    final_fare: Decimal | None = None
    currency: str = "XOF"
    distance_km: Decimal | None = None
    duration_seconds: int | None = None
    base_fare: Decimal | None = None
    distance_fare: Decimal | None = None
    duration_fare: Decimal | None = None
    surge_multiplier: Decimal = Decimal("1.00")
    surge_cap: Decimal = Decimal("1.60")
    commission_rate: Decimal = Decimal("0.08")
    driver_payout_estimate: Decimal | None = None
    platform_commission: Decimal | None = None
    actual_distance_km: Decimal | None = None
    actual_duration_seconds: int | None = None
    map_trace_id: str | None = None
    payment_method: PaymentMethod = PaymentMethod.CASH

    # Cross-module refs (logical — resolved via module APIs, never via SQL)
    driver_id: UUID | None = None
    vehicle_id: UUID | None = None
    payment_transaction_id: UUID | None = None
    share_token: str | None = None
    share_expires_at: datetime | None = None
    emergency_requested_at: datetime | None = None
    emergency_status: str | None = None
    emergency_note: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    # List of RideStatusTransition appended by `.transition()`. The service
    # layer is responsible for persisting each entry to `ride_status_history`.
    status_history: list[RideStatusTransition] = field(default_factory=list)

    @staticmethod
    def new_id() -> UUID:
        return uuid4()

    @property
    def is_active(self) -> bool:
        return self.status in {
            RideStatus.REQUESTED,
            RideStatus.MATCHED,
            RideStatus.DRIVER_EN_ROUTE,
            RideStatus.IN_PROGRESS,
        }

    def transition(
        self,
        new_status: RideStatus,
        *,
        when: datetime | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Apply a state transition. Raises `InvalidStatusTransition` if the
        move is not in `ALLOWED_TRANSITIONS`.

        Side-effects on the entity:
          - `self.status` is updated.
          - Timestamps (`matched_at`, `started_at`, `completed_at`, `cancelled_at`)
            are populated on the *first* visit to each respective state.
          - A `RideStatusTransition` is appended to `self.status_history`
            (persisted by the service layer via the repository).

        The service layer must still persist the entity + the history row.
        """
        allowed = ALLOWED_TRANSITIONS.get(self.status, set())
        if new_status == self.status:
            return  # no-op for identical status
        if new_status not in allowed:
            raise InvalidStatusTransition(
                f"Cannot transition from {self.status.value} to {new_status.value}."
            )
        now = when or datetime.utcnow()
        from_status = self.status
        self.status = new_status
        if new_status == RideStatus.MATCHED and self.matched_at is None:
            self.matched_at = now
        if new_status == RideStatus.IN_PROGRESS and self.started_at is None:
            self.started_at = now
        if new_status == RideStatus.COMPLETED and self.completed_at is None:
            self.completed_at = now
            if self.final_fare is None and self.estimated_fare is not None:
                self.final_fare = self.estimated_fare
        is_cancellation = new_status in {
            RideStatus.CANCELLED_BY_PASSENGER,
            RideStatus.CANCELLED_BY_DRIVER,
        }
        if is_cancellation and self.cancelled_at is None:
            self.cancelled_at = now
        self.status_history.append(
            RideStatusTransition(
                ride_id=self.id,
                from_status=from_status,
                to_status=new_status,
                changed_at=now,
                metadata=metadata,
            )
        )


@dataclass
class DriverProfile:
    id: UUID
    user_id: UUID
    license_number: str
    status: DriverStatus = DriverStatus.PENDING_VERIFICATION
    rating_avg: Decimal | None = Decimal("5.00")
    rating_count: int = 0
    license_verified_at: datetime | None = None
    legal_name: str | None = None
    birth_date: date | None = None
    residence_address: str | None = None
    license_document_file_id: UUID | None = None
    national_id_document_file_id: UUID | None = None
    selfie_document_file_id: UUID | None = None
    license_document_url: str | None = None
    national_id_document_url: str | None = None
    selfie_document_url: str | None = None
    kyc_submitted_at: datetime | None = None
    kyc_reviewed_at: datetime | None = None
    kyc_review_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class Vehicle:
    id: UUID
    driver_id: UUID
    plate_number: str
    category: VehicleCategory = VehicleCategory.STANDARD
    comfort_level: ComfortLevel = ComfortLevel.STANDARD
    make: str | None = None
    model: str | None = None
    color: str | None = None
    registration_document_file_id: UUID | None = None
    active: bool = True
    created_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class PricingRule:
    id: UUID
    city: str
    vehicle_category: VehicleCategory
    base_fare: Decimal
    price_per_km: Decimal
    price_per_min: Decimal
    min_fare: Decimal
    surge_multiplier: Decimal = Decimal("1.00")
    active_from: datetime | None = None
    active_to: datetime | None = None


@dataclass
class RideRating:
    id: UUID
    ride_id: UUID
    rater_role: str  # 'passenger' | 'driver'
    rating: int
    comment: str | None = None
    created_at: datetime | None = None


@dataclass
class RideRoutePoint:
    ride_id: UUID
    location: GeoPoint
    recorded_at: datetime
    heading: int | None = None
    speed_kmh: Decimal | None = None
    accuracy_m: Decimal | None = None
    source: str = "driver"
    extra: dict | None = None


@dataclass
class RideStatusTransition:
    """One row in ride.ride_status_history. Stored as a plain dataclass here
    so the domain layer doesn't depend on SQLAlchemy."""

    ride_id: UUID
    from_status: RideStatus | None
    to_status: RideStatus
    changed_at: datetime
    metadata: dict | None = None
