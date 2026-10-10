from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.comms_task_resolver import RideCommsTaskResolver

RIDE_ID = UUID("11111111-1111-1111-1111-111111111111")
PASSENGER_ID = UUID("22222222-2222-2222-2222-222222222222")
DRIVER_PROFILE_ID = UUID("33333333-3333-3333-3333-333333333333")
DRIVER_USER_ID = UUID("44444444-4444-4444-4444-444444444444")


class FakeSession:
    def __init__(self, values: dict[tuple[type, UUID], object]) -> None:
        self.values = values

    async def get(self, model: type, object_id: UUID):
        return self.values.get((model, object_id))


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolver_returns_active_ride_participants_and_permissions() -> None:
    from app_base.modules.auth.infra.models import UserModel
    from app_base.modules.ride.infra.models import DriverProfileModel, RideModel

    session = FakeSession(
        {
            (RideModel, RIDE_ID): _ride(status="matched"),
            (UserModel, PASSENGER_ID): SimpleNamespace(phone="+237600000001"),
            (DriverProfileModel, DRIVER_PROFILE_ID): SimpleNamespace(user_id=DRIVER_USER_ID),
            (UserModel, DRIVER_USER_ID): SimpleNamespace(phone="+237600000002"),
        }
    )

    projection = await RideCommsTaskResolver(session).resolve(task_type="ride", task_id=RIDE_ID)  # type: ignore[arg-type]

    assert projection.owner_service == "diddigo"
    assert projection.task_type == "ride"
    assert projection.task_id == RIDE_ID
    assert projection.state == "driver_assigned"
    assert projection.messaging_allowed is True
    assert projection.calling_allowed is True
    assert projection.closes_at is None
    assert [(participant.user_id, participant.role) for participant in projection.participants] == [
        (PASSENGER_ID, "passenger"),
        (DRIVER_USER_ID, "driver"),
    ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolver_closes_completed_ride_after_grace_period() -> None:
    from app_base.modules.auth.infra.models import UserModel
    from app_base.modules.ride.infra.models import DriverProfileModel, RideModel

    completed_at = datetime.now(UTC) - timedelta(hours=49)
    session = FakeSession(
        {
            (RideModel, RIDE_ID): _ride(status="completed", completed_at=completed_at),
            (UserModel, PASSENGER_ID): SimpleNamespace(phone="+237600000001"),
            (DriverProfileModel, DRIVER_PROFILE_ID): SimpleNamespace(user_id=DRIVER_USER_ID),
            (UserModel, DRIVER_USER_ID): SimpleNamespace(phone="+237600000002"),
        }
    )

    projection = await RideCommsTaskResolver(session).resolve(task_type="ride", task_id=RIDE_ID)  # type: ignore[arg-type]

    assert projection.messaging_allowed is False
    assert projection.calling_allowed is False
    assert projection.closes_at == completed_at + timedelta(hours=48)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolver_allows_arrived_ride_communications() -> None:
    from app_base.modules.auth.infra.models import UserModel
    from app_base.modules.ride.infra.models import DriverProfileModel, RideModel

    session = FakeSession(
        {
            (RideModel, RIDE_ID): _ride(status="arrived"),
            (UserModel, PASSENGER_ID): SimpleNamespace(phone="+237600000001"),
            (DriverProfileModel, DRIVER_PROFILE_ID): SimpleNamespace(user_id=DRIVER_USER_ID),
            (UserModel, DRIVER_USER_ID): SimpleNamespace(phone="+237600000002"),
        }
    )

    projection = await RideCommsTaskResolver(session).resolve(task_type="ride", task_id=RIDE_ID)  # type: ignore[arg-type]

    assert projection.messaging_allowed is True
    assert projection.calling_allowed is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolver_keeps_chat_but_disables_calls_during_terminal_grace_period() -> None:
    from app_base.modules.auth.infra.models import UserModel
    from app_base.modules.ride.infra.models import DriverProfileModel, RideModel

    session = FakeSession(
        {
            (RideModel, RIDE_ID): _ride(status="completed", completed_at=datetime.now(UTC)),
            (UserModel, PASSENGER_ID): SimpleNamespace(phone="+237600000001"),
            (DriverProfileModel, DRIVER_PROFILE_ID): SimpleNamespace(user_id=DRIVER_USER_ID),
            (UserModel, DRIVER_USER_ID): SimpleNamespace(phone="+237600000002"),
        }
    )

    projection = await RideCommsTaskResolver(session).resolve(task_type="ride", task_id=RIDE_ID)  # type: ignore[arg-type]

    assert projection.messaging_allowed is True
    assert projection.calling_allowed is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolver_rejects_unsupported_task_type() -> None:
    with pytest.raises(ApiError) as exc:
        await RideCommsTaskResolver(FakeSession({})).resolve(task_type="delivery", task_id=RIDE_ID)  # type: ignore[arg-type]

    assert exc.value.status_code == 422
    assert exc.value.code == "COMMS_TASK_TYPE_UNSUPPORTED"


def _ride(
    *,
    status: str,
    completed_at: datetime | None = None,
    cancelled_at: datetime | None = None,
):
    now = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
    return SimpleNamespace(
        id=RIDE_ID,
        passenger_user_id=PASSENGER_ID,
        driver_id=DRIVER_PROFILE_ID,
        status=status,
        completed_at=completed_at,
        cancelled_at=cancelled_at,
        updated_at=now,
        requested_at=now,
    )
