"""SQLAlchemy-backed ride repositories (batch 5 infrastructure).

Maps between `ride.domain.entities` dataclasses and the ORM models in
`ride.infra.models`. Geography conversion (PostGIS ↔ `GeoPoint`) lives here:
    - write: `Geography` column receives a `WKBElement` from `from_shape(Point(lng, lat))`
    - read: `to_shape(wkb_element)` returns a shapely `Point(x=lng, y=lat)`
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.ride.domain.entities import (
    DriverProfile,
    DriverStatus,
    PricingRule,
    Ride,
    RideRating,
    RideStatus,
    RideStatusTransition,
    Vehicle,
    VehicleCategory,
)
from app_base.modules.ride.infra import models as orm
from app_base.shared_kernel.types import GeoPoint

_ACTIVE_STATES = {
    RideStatus.REQUESTED,
    RideStatus.MATCHED,
    RideStatus.DRIVER_EN_ROUTE,
    RideStatus.IN_PROGRESS,
}


def _to_orm_geo(point: GeoPoint) -> object:
    # GeoAlchemy2 + PostGIS: store points with (lng, lat) order — shapely's
    # Point takes (x=lng, y=lat). WGS84 SRID 4326.
    return from_shape(Point(point.lng, point.lat), srid=4326)


def _from_orm_geo(value: object) -> GeoPoint:
    pt = to_shape(value)
    return GeoPoint(lat=float(pt.y), lng=float(pt.x))


# ---------------------------------------------------------------------------
# Rides
# ---------------------------------------------------------------------------

class SqlAlchemyRideRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, ride: Ride) -> Ride:
        row: orm.RideModel | None = await self._session.get(orm.RideModel, ride.id)
        if row is None:
            row = orm.RideModel(id=ride.id)
            self._session.add(row)
        self._apply(row, ride)
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        return ride

    async def find_by_id(self, ride_id: UUID) -> Ride | None:
        row = await self._session.get(orm.RideModel, ride_id)
        if row is None:
            return None
        return self._to_domain(row)

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
        q = select(orm.RideModel)
        if passenger_user_id is not None:
            q = q.where(orm.RideModel.passenger_user_id == passenger_user_id)
        if driver_id is not None:
            q = q.where(orm.RideModel.driver_id == driver_id)
        if status is not None:
            q = q.where(orm.RideModel.status == status.value)
        if from_date is not None:
            q = q.where(orm.RideModel.requested_at >= from_date)
        if to_date is not None:
            q = q.where(orm.RideModel.requested_at < to_date)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._session.execute(count_q)).scalar() or 0

        q = q.order_by(orm.RideModel.requested_at.desc())
        q = q.offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(q)
        rides = [self._to_domain(r) for r in result.scalars().all()]
        return rides, int(total)

    async def has_active_ride(self, passenger_user_id: UUID) -> bool:
        statuses = [s.value for s in _ACTIVE_STATES]
        result = await self._session.execute(
            select(func.count(orm.RideModel.id)).where(
                orm.RideModel.passenger_user_id == passenger_user_id,
                orm.RideModel.status.in_(statuses),
            ),
        )
        return (result.scalar_one() or 0) > 0

    async def record_status_transition(self, transition: RideStatusTransition) -> None:
        row = orm.RideStatusHistoryModel(
            id=Ride.new_id(),
            ride_id=transition.ride_id,
            from_status=transition.from_status.value if transition.from_status else None,
            to_status=transition.to_status.value,
            changed_at=transition.changed_at,
            extra=transition.metadata,
        )
        self._session.add(row)
        await self._session.flush()

    async def save_rating(self, rating: RideRating) -> RideRating:
        row = orm.RideRatingModel(
            id=rating.id,
            ride_id=rating.ride_id,
            rater_role=rating.rater_role,
            rating=rating.rating,
            comment=rating.comment,
            created_at=rating.created_at or datetime.now(UTC),
        )
        self._session.add(row)
        await self._session.flush()
        return rating

    async def has_rated(self, ride_id: UUID, rater_role: str) -> bool:
        result = await self._session.execute(
            select(func.count(orm.RideRatingModel.id)).where(
                orm.RideRatingModel.ride_id == ride_id,
                orm.RideRatingModel.rater_role == rater_role,
            ),
        )
        return (result.scalar_one() or 0) > 0

    # -- mapping helpers -----------------------------------------------------

    @staticmethod
    def _apply(row: orm.RideModel, ride: Ride) -> None:
        row.passenger_user_id = ride.passenger_user_id
        row.status = ride.status.value
        row.pickup_location = _to_orm_geo(ride.pickup_location) if ride.pickup_location else row.pickup_location  # type: ignore[assignment]
        row.pickup_address = ride.pickup_address
        row.dropoff_location = _to_orm_geo(ride.dropoff_location) if ride.dropoff_location else row.dropoff_location  # type: ignore[assignment]
        row.dropoff_address = ride.dropoff_address
        row.scheduled_at = ride.scheduled_at
        row.requested_at = ride.requested_at or datetime.now(UTC)
        row.matched_at = ride.matched_at
        row.started_at = ride.started_at
        row.completed_at = ride.completed_at
        row.cancelled_at = ride.cancelled_at
        row.cancellation_reason = ride.cancellation_reason
        row.estimated_fare = ride.estimated_fare
        row.final_fare = ride.final_fare
        row.currency = ride.currency
        row.distance_km = ride.distance_km
        row.duration_seconds = ride.duration_seconds
        row.driver_id = ride.driver_id
        row.vehicle_id = ride.vehicle_id
        row.payment_transaction_id = ride.payment_transaction_id

    @classmethod
    def _to_domain(cls, row: orm.RideModel) -> Ride:
        return Ride(
            id=row.id,
            passenger_user_id=row.passenger_user_id,
            status=RideStatus(row.status),
            # `ride.rides` has no vehicle_category column in the spec — the
            # category belongs to the assigned vehicle, so it is only known
            # once a driver is matched.
            vehicle_category=VehicleCategory.STANDARD,
            pickup_location=_from_orm_geo(row.pickup_location) if row.pickup_location is not None else None,
            pickup_address=row.pickup_address,
            dropoff_location=_from_orm_geo(row.dropoff_location) if row.dropoff_location is not None else None,
            dropoff_address=row.dropoff_address,
            scheduled_at=row.scheduled_at,
            requested_at=row.requested_at,
            matched_at=row.matched_at,
            started_at=row.started_at,
            completed_at=row.completed_at,
            cancelled_at=row.cancelled_at,
            cancellation_reason=row.cancellation_reason,
            estimated_fare=Decimal(str(row.estimated_fare)) if row.estimated_fare is not None else None,
            final_fare=Decimal(str(row.final_fare)) if row.final_fare is not None else None,
            currency=row.currency,
            distance_km=Decimal(str(row.distance_km)) if row.distance_km is not None else None,
            duration_seconds=row.duration_seconds,
            driver_id=row.driver_id,
            vehicle_id=row.vehicle_id,
            payment_transaction_id=row.payment_transaction_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


# ---------------------------------------------------------------------------
# Drivers / vehicles / pricing
# ---------------------------------------------------------------------------

class SqlAlchemyDriverProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, profile: DriverProfile) -> DriverProfile:
        row: orm.DriverProfileModel | None = await self._session.get(
            orm.DriverProfileModel, profile.id,
        )
        if row is None:
            row = orm.DriverProfileModel(id=profile.id)
            self._session.add(row)
        row.user_id = profile.user_id
        row.license_number = profile.license_number
        row.status = profile.status.value
        row.rating_avg = profile.rating_avg
        row.rating_count = profile.rating_count
        row.license_verified_at = profile.license_verified_at
        row.legal_name = profile.legal_name
        row.birth_date = profile.birth_date
        row.residence_address = profile.residence_address
        row.license_document_file_id = profile.license_document_file_id
        row.national_id_document_file_id = profile.national_id_document_file_id
        row.selfie_document_file_id = profile.selfie_document_file_id
        row.license_document_url = profile.license_document_url
        row.national_id_document_url = profile.national_id_document_url
        row.selfie_document_url = profile.selfie_document_url
        row.kyc_submitted_at = profile.kyc_submitted_at
        row.kyc_reviewed_at = profile.kyc_reviewed_at
        row.kyc_review_notes = profile.kyc_review_notes
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        return profile

    async def find_by_user_id(self, user_id: UUID) -> DriverProfile | None:
        result = await self._session.execute(
            select(orm.DriverProfileModel).where(orm.DriverProfileModel.user_id == user_id),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def find_by_id(self, profile_id: UUID) -> DriverProfile | None:
        row = await self._session.get(orm.DriverProfileModel, profile_id)
        if row is None:
            return None
        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: orm.DriverProfileModel) -> DriverProfile:
        return DriverProfile(
            id=row.id,
            user_id=row.user_id,
            license_number=row.license_number,
            status=DriverStatus(row.status),
            rating_avg=row.rating_avg,
            rating_count=row.rating_count,
            license_verified_at=row.license_verified_at,
            legal_name=row.legal_name,
            birth_date=row.birth_date,
            residence_address=row.residence_address,
            license_document_file_id=row.license_document_file_id,
            national_id_document_file_id=row.national_id_document_file_id,
            selfie_document_file_id=row.selfie_document_file_id,
            license_document_url=row.license_document_url,
            national_id_document_url=row.national_id_document_url,
            selfie_document_url=row.selfie_document_url,
            kyc_submitted_at=row.kyc_submitted_at,
            kyc_reviewed_at=row.kyc_reviewed_at,
            kyc_review_notes=row.kyc_review_notes,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class SqlAlchemyVehicleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, vehicle: Vehicle) -> Vehicle:
        row = orm.VehicleModel(
            id=vehicle.id,
            driver_id=vehicle.driver_id,
            plate_number=vehicle.plate_number,
            make=vehicle.make,
            model=vehicle.model,
            color=vehicle.color,
            registration_document_file_id=vehicle.registration_document_file_id,
            category=vehicle.category.value,
            active=vehicle.active,
        )
        self._session.add(row)
        await self._session.flush()
        return vehicle

    async def find_active_for_driver(self, driver_id: UUID) -> Vehicle | None:
        result = await self._session.execute(
            select(orm.VehicleModel).where(
                orm.VehicleModel.driver_id == driver_id,
                orm.VehicleModel.active.is_(True),
            ).limit(1),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return Vehicle(
            id=row.id,
            driver_id=row.driver_id,
            plate_number=row.plate_number,
            category=VehicleCategory(row.category),
            make=row.make,
            model=row.model,
            color=row.color,
            registration_document_file_id=row.registration_document_file_id,
            active=row.active,
            created_at=row.created_at,
        )


class SqlAlchemyPricingRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_active(
        self,
        city: str,
        vehicle_category: VehicleCategory,
        as_of: datetime | None = None,
    ) -> PricingRule | None:
        now = as_of or datetime.now(UTC)
        result = await self._session.execute(
            select(orm.PricingRuleModel).where(
                orm.PricingRuleModel.city == city,
                orm.PricingRuleModel.vehicle_category == vehicle_category.value,
                orm.PricingRuleModel.active_from <= now,
                (orm.PricingRuleModel.active_to.is_(None) | (orm.PricingRuleModel.active_to >= now)),
            ).order_by(orm.PricingRuleModel.active_from.desc()).limit(1),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return PricingRule(
            id=row.id,
            city=row.city,
            vehicle_category=VehicleCategory(row.vehicle_category),
            base_fare=row.base_fare,
            price_per_km=row.price_per_km,
            price_per_min=row.price_per_min,
            min_fare=row.min_fare,
            surge_multiplier=row.surge_multiplier,
            active_from=row.active_from,
            active_to=row.active_to,
        )
