"""Privacy-preserving ride context projection for DiddiSupport.

The projection intentionally has no contact details, KYC data, raw location or
payment-provider identifiers. DiddiSupport receives only what it needs to
understand and triage a ride case.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.errors import ApiError
from app_base.modules.ride.infra.models import DriverProfileModel, RideModel


@dataclass(frozen=True)
class SupportParticipantProjection:
    user_id: UUID
    role: str


@dataclass(frozen=True)
class SupportRideContextProjection:
    ride_id: UUID
    status: str
    completion_reason: str | None
    cancellation_reason: str | None
    fare_amount: Decimal | None
    currency: str
    payment_method: str
    participants: list[SupportParticipantProjection]
    requested_at: datetime | None
    matched_at: datetime | None
    arrived_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    as_of: datetime


class RideSupportContextResolver:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve(self, ride_id: UUID) -> SupportRideContextProjection:
        ride = await self.session.get(RideModel, ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Course introuvable.")

        participants = [SupportParticipantProjection(user_id=ride.passenger_user_id, role="passenger")]
        if ride.driver_id is not None:
            driver = await self.session.get(DriverProfileModel, ride.driver_id)
            if driver is not None:
                participants.append(SupportParticipantProjection(user_id=driver.user_id, role="driver"))

        return SupportRideContextProjection(
            ride_id=ride.id,
            status=ride.status,
            completion_reason=ride.completion_reason,
            cancellation_reason=ride.cancellation_reason,
            fare_amount=ride.final_fare if ride.final_fare is not None else ride.estimated_fare,
            currency=ride.currency,
            payment_method=ride.payment_method,
            participants=participants,
            requested_at=ride.requested_at,
            matched_at=ride.matched_at,
            arrived_at=ride.arrived_at,
            started_at=ride.started_at,
            completed_at=ride.completed_at,
            cancelled_at=ride.cancelled_at,
            as_of=_as_utc(ride.updated_at or ride.completed_at or ride.cancelled_at or ride.requested_at),
        )


def _as_utc(value: datetime | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
