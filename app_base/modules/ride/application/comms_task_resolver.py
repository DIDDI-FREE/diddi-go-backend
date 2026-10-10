from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.errors import ApiError
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.domain.entities import RideStatus
from app_base.modules.ride.infra.models import DriverProfileModel, RideModel

RIDE_COMMS_GRACE_PERIOD = timedelta(hours=48)
ACTIVE_COMMS_STATUSES = {
    RideStatus.MATCHED.value,
    RideStatus.DRIVER_EN_ROUTE.value,
    RideStatus.ARRIVED.value,
    RideStatus.IN_PROGRESS.value,
    RideStatus.WAITING.value,
}
TERMINAL_WITH_GRACE_STATUSES = {
    RideStatus.COMPLETED.value,
    RideStatus.CANCELLED_BY_PASSENGER.value,
    RideStatus.CANCELLED_BY_DRIVER.value,
}


@dataclass(frozen=True)
class CommsParticipantProjection:
    user_id: UUID
    role: str
    phone_e164: str | None


@dataclass(frozen=True)
class CommsTaskProjection:
    owner_service: str
    task_type: str
    task_id: UUID
    state: str
    version: int
    participants: list[CommsParticipantProjection]
    messaging_allowed: bool
    calling_allowed: bool
    closes_at: datetime | None


class RideCommsTaskResolver:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve(self, *, task_type: str, task_id: UUID) -> CommsTaskProjection:
        if task_type != "ride":
            raise ApiError(422, "COMMS_TASK_TYPE_UNSUPPORTED", "DiddiGo only resolves ride communication tasks.")

        ride = await self.session.get(RideModel, task_id)
        if ride is None:
            raise ApiError(404, "COMMS_TASK_NOT_FOUND", "Ride communication task was not found.")

        participants = await self._participants_for(ride)
        closes_at = _communication_closes_at(ride)
        messaging_allowed = _messaging_allowed(ride, participants=participants, closes_at=closes_at)
        calling_allowed = len(participants) >= 2 and ride.status in ACTIVE_COMMS_STATUSES
        return CommsTaskProjection(
            owner_service="diddigo",
            task_type="ride",
            task_id=ride.id,
            state=_external_state(ride.status),
            version=_version_for(ride),
            participants=participants,
            messaging_allowed=messaging_allowed,
            calling_allowed=calling_allowed,
            closes_at=closes_at,
        )

    async def _participants_for(self, ride: RideModel) -> list[CommsParticipantProjection]:
        passenger = await self.session.get(UserModel, ride.passenger_user_id)
        participants: list[CommsParticipantProjection] = [
            CommsParticipantProjection(
                user_id=ride.passenger_user_id,
                role="passenger",
                phone_e164=passenger.phone if passenger else None,
            )
        ]
        if ride.driver_id is None:
            return participants

        driver = await self.session.get(DriverProfileModel, ride.driver_id)
        if driver is None:
            return participants
        driver_user = await self.session.get(UserModel, driver.user_id)
        participants.append(
            CommsParticipantProjection(
                user_id=driver.user_id,
                role="driver",
                phone_e164=driver_user.phone if driver_user else None,
            )
        )
        return participants


def _messaging_allowed(
    ride: RideModel,
    *,
    participants: list[CommsParticipantProjection],
    closes_at: datetime | None,
) -> bool:
    if len(participants) < 2:
        return False
    if ride.status in ACTIVE_COMMS_STATUSES:
        return True
    if ride.status in TERMINAL_WITH_GRACE_STATUSES and closes_at is not None:
        return datetime.now(UTC) < closes_at.astimezone(UTC)
    return False


def _external_state(status: str) -> str:
    if status == RideStatus.MATCHED.value:
        return "driver_assigned"
    return status


def _communication_closes_at(ride: RideModel) -> datetime | None:
    if ride.status in ACTIVE_COMMS_STATUSES:
        return None
    terminal_at = ride.completed_at or ride.cancelled_at
    if ride.status in TERMINAL_WITH_GRACE_STATUSES and terminal_at is not None:
        return _aware_utc(terminal_at) + RIDE_COMMS_GRACE_PERIOD
    return None


def _version_for(ride: RideModel) -> int:
    updated_at = ride.updated_at or ride.requested_at
    if updated_at is None:
        return 0
    return int(_aware_utc(updated_at).timestamp())


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
