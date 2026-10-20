from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.support_context_resolver import RideSupportContextResolver

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
async def test_support_context_is_redacted_and_contains_operational_ride_data() -> None:
    from app_base.modules.ride.infra.models import DriverProfileModel, RideModel

    at = datetime(2026, 10, 20, 11, 0, tzinfo=UTC)
    ride = SimpleNamespace(
        id=RIDE_ID, passenger_user_id=PASSENGER_ID, driver_id=DRIVER_PROFILE_ID,
        status="completed", completion_reason="normal", cancellation_reason=None,
        estimated_fare=Decimal("3500"), final_fare=Decimal("3700"), currency="XOF",
        payment_method="mobile_money", requested_at=at, matched_at=at, arrived_at=at,
        started_at=at, completed_at=at, cancelled_at=None, updated_at=at,
    )
    session = FakeSession({
        (RideModel, RIDE_ID): ride,
        (DriverProfileModel, DRIVER_PROFILE_ID): SimpleNamespace(user_id=DRIVER_USER_ID),
    })

    context = await RideSupportContextResolver(session).resolve(RIDE_ID)  # type: ignore[arg-type]

    assert context.status == "completed"
    assert context.fare_amount == Decimal("3700")
    assert context.as_of == at
    assert [(item.user_id, item.role) for item in context.participants] == [
        (PASSENGER_ID, "passenger"), (DRIVER_USER_ID, "driver"),
    ]
    assert not hasattr(context, "pickup_location")
    assert not hasattr(context, "phone_e164")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_support_context_returns_not_found_for_unknown_ride() -> None:
    with pytest.raises(ApiError) as error:
        await RideSupportContextResolver(FakeSession({})).resolve(RIDE_ID)  # type: ignore[arg-type]

    assert error.value.status_code == 404
    assert error.value.code == "RIDE_NOT_FOUND"
