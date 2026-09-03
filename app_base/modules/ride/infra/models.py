"""Ride module — PostgreSQL tables in the `ride` schema.

Mirrors architecture doc §3.2 exactly:
    ride.driver_profiles
    ride.vehicles
    ride.rides                              (includes PostGIS GEOGRAPHY columns)
    ride.ride_status_history
    ride.ride_route_points                  (PostGIS GEOGRAPHY column)
    ride.pricing_rules
    ride.ride_ratings                       (CHECK rating 1..5, UNIQUE ride_id+rater_role)

Spatial columns (`pickup_location`, `dropoff_location`, `ride_route_points.location`)
use GeoAlchemy2 `Geography(geometry_type='POINT', srid=4326)` — WGS84 coords
in degrees, distances in meters on the sphere. This matches the architecture
doc SQL which specifies `GEOGRAPHY(POINT, 4326)`.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app_base.core.database import Base

_PG_UUID = PG_UUID(as_uuid=True)


class DriverProfileModel(Base):
    __tablename__ = "driver_profiles"
    __table_args__ = {"schema": "ride"}

    id: Mapped[UUID] = mapped_column(
        _PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"),
    )
    user_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("auth.users.id"),
        unique=True,
        nullable=False,
    )
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    license_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    legal_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    residence_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_document_file_id: Mapped[UUID | None] = mapped_column(_PG_UUID, nullable=True)
    national_id_document_file_id: Mapped[UUID | None] = mapped_column(_PG_UUID, nullable=True)
    selfie_document_file_id: Mapped[UUID | None] = mapped_column(_PG_UUID, nullable=True)
    license_document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    national_id_document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    selfie_document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    kyc_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    kyc_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    kyc_review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending_verification",
    )  # pending_verification | active | suspended | offline
    rating_avg: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("5.00"),
    )
    rating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )


class VehicleModel(Base):
    __tablename__ = "vehicles"
    __table_args__ = {"schema": "ride"}

    id: Mapped[UUID] = mapped_column(
        _PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"),
    )
    driver_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("ride.driver_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    make: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    registration_document_file_id: Mapped[UUID | None] = mapped_column(_PG_UUID, nullable=True)
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")  # standard | comfort | van
    comfort_level: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )


class RideModel(Base):
    __tablename__ = "rides"
    __table_args__ = {"schema": "ride"}

    id: Mapped[UUID] = mapped_column(
        _PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"),
    )
    passenger_user_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("auth.users.id"),
        nullable=False,
        index=True,
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        _PG_UUID,
        ForeignKey("ride.driver_profiles.id"),
        nullable=True,
    )
    vehicle_id: Mapped[UUID | None] = mapped_column(
        _PG_UUID,
        ForeignKey("ride.vehicles.id"),
        nullable=True,
    )
    # NOTE: the architecture doc specifies VARCHAR(20), but the longest status
    # value it defines — `cancelled_by_passenger` — is 22 characters, so a
    # passenger cancellation would fail at the DB level. Widened to 30 to hold
    # every value in the enum with headroom for the future `payment_pending`
    # status the API contract reserves.
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="requested")
    comfort_level: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")
    # -- Spatial columns: WGS84 geography (degrees); distances computed in meters on the sphere.
    pickup_location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    pickup_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    dropoff_location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    dropoff_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    # -- Timestamps
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # -- Pricing (XOF has no sub-unit → stored as integer-equivalent decimals)
    estimated_fare: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    final_fare: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="XOF")
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)  # from DiddiMap
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)  # from DiddiMap
    base_fare: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    distance_fare: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    duration_fare: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    surge_multiplier: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("1.00"))
    surge_cap: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("1.60"))
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("0.08"))
    driver_payout_estimate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    platform_commission: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    actual_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    actual_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_pricing_fare: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    pricing_delta: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    map_trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False, default="cash")
    # -- Cross-module reference (resolved via payment_module, never via direct SQL)
    payment_transaction_id: Mapped[UUID | None] = mapped_column(_PG_UUID, nullable=True)
    share_token: Mapped[str | None] = mapped_column(String(80), nullable=True, unique=True)
    share_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    emergency_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    emergency_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    emergency_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )


class RideStatusHistoryModel(Base):
    __tablename__ = "ride_status_history"
    __table_args__ = {"schema": "ride"}

    id: Mapped[UUID] = mapped_column(
        _PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"),
    )
    ride_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("ride.rides.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Same widening as ride.rides.status — see the note there.
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )
    # SQLAlchemy Declarative reserves the `metadata` attribute name on `Table`.
    # The column is named `metadata` in the DB, but accessible in Python as
    # `extra` (mapped via the positional name arg of mapped_column).
    extra: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class RideRoutePointModel(Base):
    """Sampled trajectory points along a completed ride — stored at low frequency
    (not the high-rate live stream, which stays in Redis). Architecture doc §3.2."""

    __tablename__ = "ride_route_points"
    __table_args__ = {"schema": "ride"}

    # BIGSERIAL — SQLAlchemy maps `BigInteger` + primary key to `BIGSERIAL`
    # on PostgreSQL when the column has an integer default strategy. Route
    # points are insert-only and indexed by `(ride_id, recorded_at)` for
    # time-series queries.
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    ride_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("ride.rides.id", ondelete="CASCADE"),
        nullable=False,
    )
    location = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    heading: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed_kmh: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    accuracy_m: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="driver")
    extra: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class PricingRuleModel(Base):
    """Per-city, per-vehicle-category fare configuration. Architecture doc §3.2."""

    __tablename__ = "pricing_rules"
    __table_args__ = {"schema": "ride"}

    id: Mapped[UUID] = mapped_column(
        _PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"),
    )
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_category: Mapped[str] = mapped_column(
        String(20), nullable=False, default="standard",
    )
    base_fare: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_per_km: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_per_min: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_fare: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    surge_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("1.00"),
    )  # capped by product policy — see infra doc §plafond x1.6
    active_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )
    active_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RideRatingModel(Base):
    """Post-ride rating. One per role per ride (UNIQUE constraint enforced at DB
    level). Architecture doc §3.2 — CHECK 1..5 on the rating column."""

    __tablename__ = "ride_ratings"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ride_ratings_rating_check"),
        UniqueConstraint("ride_id", "rater_role", name="ride_ratings_ride_rater_unique"),
        {"schema": "ride"},
    )

    id: Mapped[UUID] = mapped_column(
        _PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"),
    )
    ride_id: Mapped[UUID] = mapped_column(
        _PG_UUID,
        ForeignKey("ride.rides.id", ondelete="CASCADE"),
        nullable=False,
    )
    rater_role: Mapped[str] = mapped_column(
        String(10), nullable=False,
    )  # 'passenger' | 'driver'
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )
