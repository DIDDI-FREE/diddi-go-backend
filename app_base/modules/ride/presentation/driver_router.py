"""Driver router — `/v1/drivers/*`.

Onboarding (profile + vehicle) and availability (go online / offline).
Every route is driver-only: a passenger token gets `403 FORBIDDEN_ROLE`.

These endpoints are the prerequisite for matching — a ride can only be
assigned to a driver who has a verified profile, an active vehicle, and a
live position in the Redis pool.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app_base.core.auth_deps import require_role
from app_base.core.deps import driver_service, get_driver_locations
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.application.driver_service import DriverService
from app_base.modules.ride.infra.driver_location import RedisDriverLocationService
from app_base.modules.ride.presentation.driver_schemas import (
    DriverProfileCreateRequest,
    GoOnlineRequest,
    VehicleCreateRequest,
)
from app_base.shared_kernel.types import GeoPoint

router = APIRouter(prefix="/drivers", tags=["driver"])


@router.post("/profile", status_code=201)
async def create_profile(
    payload: DriverProfileCreateRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(require_role("driver")),
) -> dict:
    return await service.create_profile(
        user_id=current_user.id,
        license_number=payload.license_number,
    )


@router.post("/vehicle", status_code=201)
async def register_vehicle(
    payload: VehicleCreateRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(require_role("driver")),
) -> dict:
    return await service.register_vehicle(
        user_id=current_user.id,
        plate_number=payload.plate_number,
        make=payload.make,
        model=payload.model,
        color=payload.color,
        category=payload.category,
    )


@router.get("/me")
async def get_my_profile(
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(require_role("driver")),
) -> dict:
    return await service.get_profile(current_user.id)


@router.post("/online")
async def go_online(
    payload: GoOnlineRequest,
    service: DriverService = Depends(driver_service),
    locations: RedisDriverLocationService = Depends(get_driver_locations),
    current_user: UserModel = Depends(require_role("driver")),
) -> dict:
    """Enter the matching pool. Rejected unless the driver is verified and
    has an active vehicle — matching must never offer a ride to a driver who
    cannot legally take it."""
    profile, vehicle = await service.resolve_driver(current_user.id)
    position = GeoPoint(lat=payload.lat, lng=payload.lng)
    await locations.update_position(current_user.id, position)
    await locations.set_available(current_user.id, available=True)
    return {
        "status": "online",
        "driver_id": str(profile.id),
        "vehicle_id": str(vehicle.id),
        "location": {"lat": position.lat, "lng": position.lng},
    }


@router.post("/offline")
async def go_offline(
    locations: RedisDriverLocationService = Depends(get_driver_locations),
    current_user: UserModel = Depends(require_role("driver")),
) -> dict:
    await locations.go_offline(current_user.id)
    return {"status": "offline"}
