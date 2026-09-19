from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI

from app_base.core.auth_deps import get_current_user
from app_base.core.deps import ride_service
from app_base.core.errors import ApiError, api_error_handler
from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.domain.entities import DriverProfile, DriverStatus, Ride, RideStatus
from app_base.modules.ride.presentation.router import router as ride_router

pytestmark = pytest.mark.unit


PASSENGER_ID = uuid4()
DRIVER_USER_ID = uuid4()
DRIVER_PROFILE_ID = uuid4()
OTHER_USER_ID = uuid4()
RIDE_ID = uuid4()


class FakeRideRepo:
    def __init__(self, ride: Ride) -> None:
        self.ride = ride
        self.last_list_filters: dict | None = None

    async def find_by_id(self, ride_id: UUID) -> Ride | None:
        return self.ride if ride_id == self.ride.id else None

    async def list_by(self, **filters):
        self.last_list_filters = filters
        if filters.get("driver_id") == self.ride.driver_id:
            return [self.ride], 1
        if filters.get("passenger_user_id") == self.ride.passenger_user_id:
            return [self.ride], 1
        return [], 0


class FakeDriverRepo:
    async def find_by_user_id(self, user_id: UUID) -> DriverProfile | None:
        if user_id != DRIVER_USER_ID:
            return None
        return DriverProfile(
            id=DRIVER_PROFILE_ID,
            user_id=DRIVER_USER_ID,
            license_number="CI-BUSINESS",
            status=DriverStatus.ACTIVE,
        )

    async def find_by_id(self, profile_id: UUID) -> DriverProfile | None:
        if profile_id != DRIVER_PROFILE_ID:
            return None
        return DriverProfile(
            id=DRIVER_PROFILE_ID,
            user_id=DRIVER_USER_ID,
            license_number="CI-BUSINESS",
            status=DriverStatus.ACTIVE,
        )


def service_with(ride: Ride) -> RideService:
    return RideService(
        ride_repo=FakeRideRepo(ride),
        routing=None,
        pricing_rules=None,
        driver_repo=FakeDriverRepo(),
    )


def matched_ride() -> Ride:
    return Ride(
        id=RIDE_ID,
        passenger_user_id=PASSENGER_ID,
        status=RideStatus.MATCHED,
        driver_id=DRIVER_PROFILE_ID,
    )


@pytest.mark.asyncio
async def test_business_driver_user_can_read_assigned_ride_detail() -> None:
    result = await service_with(matched_ride()).get_ride(
        RIDE_ID,
        actor_user_id=DRIVER_USER_ID,
        actor_role="passenger",
    )

    assert result["id"] == str(RIDE_ID)
    assert result["status"] == "matched"


@pytest.mark.asyncio
async def test_unassigned_user_cannot_read_someone_elses_ride_detail() -> None:
    with pytest.raises(ApiError) as exc_info:
        await service_with(matched_ride()).get_ride(
            RIDE_ID,
            actor_user_id=OTHER_USER_ID,
            actor_role="passenger",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "RIDE_NOT_OWNED_BY_USER"


@pytest.mark.asyncio
async def test_business_driver_user_role_lists_assigned_driver_rides() -> None:
    service = service_with(matched_ride())

    result = await service.list_rides(
        actor_user_id=DRIVER_USER_ID,
        actor_role="driver",
        page=1,
        page_size=20,
    )

    assert result["pagination"]["total_items"] == 1
    assert result["data"][0]["id"] == str(RIDE_ID)
    assert service.ride_repo.last_list_filters["driver_id"] == DRIVER_PROFILE_ID


@pytest.mark.asyncio
async def test_user_cannot_select_admin_ride_view() -> None:
    service = service_with(matched_ride())

    with pytest.raises(ApiError) as exc_info:
        await service.list_rides(
            actor_user_id=OTHER_USER_ID,
            actor_role="user",
            view_role="admin",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "FORBIDDEN_ROLE"
    assert service.ride_repo.last_list_filters is None


@pytest.mark.asyncio
async def test_user_can_select_own_driver_ride_view() -> None:
    service = service_with(matched_ride())

    result = await service.list_rides(
        actor_user_id=DRIVER_USER_ID,
        actor_role="user",
        view_role="driver",
    )

    assert result["pagination"]["total_items"] == 1
    assert service.ride_repo.last_list_filters["driver_id"] == DRIVER_PROFILE_ID
    assert service.ride_repo.last_list_filters["passenger_user_id"] is None


def ride_list_app(service: RideService, *, user_id: UUID, role: str) -> FastAPI:
    app = FastAPI()
    app.include_router(ride_router, prefix="/v1")
    app.add_exception_handler(ApiError, api_error_handler)
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id, role=role)
    app.dependency_overrides[ride_service] = lambda: service
    return app


@pytest.mark.asyncio
async def test_verified_admin_can_list_all_rides() -> None:
    service = service_with(matched_ride())

    await service.list_rides(actor_user_id=OTHER_USER_ID, actor_role="admin")

    assert service.ride_repo.last_list_filters["driver_id"] is None
    assert service.ride_repo.last_list_filters["passenger_user_id"] is None


@pytest.mark.asyncio
async def test_user_cannot_select_another_driver_by_id() -> None:
    service = service_with(matched_ride())

    result = await service.list_rides(
        actor_user_id=OTHER_USER_ID,
        actor_role="user",
        view_role="driver",
        driver_id=DRIVER_PROFILE_ID,
    )

    assert result["pagination"]["total_items"] == 0
    assert service.ride_repo.last_list_filters is None


@pytest.mark.asyncio
async def test_http_user_cannot_escalate_ride_list_with_role_query() -> None:
    service = service_with(matched_ride())
    app = ride_list_app(service, user_id=OTHER_USER_ID, role="user")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/rides?role=admin")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"
    assert service.ride_repo.last_list_filters is None


@pytest.mark.asyncio
async def test_http_user_can_list_own_driver_rides() -> None:
    service = service_with(matched_ride())
    app = ride_list_app(service, user_id=DRIVER_USER_ID, role="user")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/rides?role=driver")

    assert response.status_code == 200
    assert response.json()["pagination"]["total_items"] == 1
    assert service.ride_repo.last_list_filters["driver_id"] == DRIVER_PROFILE_ID


@pytest.mark.asyncio
async def test_http_verified_admin_can_list_all_rides() -> None:
    service = service_with(matched_ride())
    app = ride_list_app(service, user_id=OTHER_USER_ID, role="admin")

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/rides?role=admin")

    assert response.status_code == 200
    assert service.ride_repo.last_list_filters["driver_id"] is None
    assert service.ride_repo.last_list_filters["passenger_user_id"] is None
