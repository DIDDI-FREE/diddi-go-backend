"""Driver router — `/v1/drivers/*`.

Onboarding (profile + vehicle) and availability (go online / offline).
Every route is driver-only: a passenger token gets `403 FORBIDDEN_ROLE`.

These endpoints are the prerequisite for matching — a ride can only be
assigned to a driver who has a verified profile, an active vehicle, and a
live position in the Redis pool.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app_base.core.auth_deps import get_current_active_user, require_business_driver
from app_base.core.deps import driver_service, get_driver_locations
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.application.driver_service import DriverService
from app_base.modules.ride.domain.entities import DriverProfile
from app_base.modules.ride.infra.driver_location import RedisDriverLocationService
from app_base.modules.ride.presentation.driver_schemas import (
    DriverProfileCreateRequest,
    GoOnlineRequest,
    VehicleCreateRequest,
)
from app_base.shared_kernel.types import GeoPoint

router = APIRouter(prefix="/drivers", tags=["driver"])
logger = logging.getLogger("uvicorn.error")


@router.post("/profile", status_code=201)
async def create_profile(
    payload: DriverProfileCreateRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.create_profile(
        user_id=current_user.id,
        license_number=payload.license_number,
        legal_name=payload.legal_name,
        birth_date=payload.birth_date,
        residence_address=payload.residence_address,
        license_document_file_id=payload.license_document_file_id,
        national_id_document_file_id=payload.national_id_document_file_id,
        selfie_document_file_id=payload.selfie_document_file_id,
        license_document_url=payload.license_document_url,
        national_id_document_url=payload.national_id_document_url,
        selfie_document_url=payload.selfie_document_url,
    )


@router.post("/vehicle", status_code=201)
async def register_vehicle(
    payload: VehicleCreateRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.register_vehicle(
        user_id=current_user.id,
        plate_number=payload.plate_number,
        make=payload.make,
        model=payload.model,
        color=payload.color,
        category=payload.category,
        comfort_level=payload.comfort_level,
        registration_document_file_id=payload.registration_document_file_id,
    )


@router.get("/me")
async def get_my_profile(
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.get_profile(current_user.id)


@router.post("/online")
async def go_online(
    payload: GoOnlineRequest,
    service: DriverService = Depends(driver_service),
    locations: RedisDriverLocationService = Depends(get_driver_locations),
    current_user: UserModel = Depends(get_current_active_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    """Enter the matching pool. Rejected unless the driver is verified and
    has an active vehicle — matching must never offer a ride to a driver who
    cannot legally take it."""
    profile, vehicle = await service.resolve_driver(current_user.id)
    position = GeoPoint(lat=payload.lat, lng=payload.lng)
    await locations.update_position(current_user.id, position)
    await locations.set_available(current_user.id, available=True)
    logger.info(
        "driver_online user_id=%s driver_profile_id=%s vehicle_id=%s lat=%s lng=%s",
        current_user.id,
        profile.id,
        vehicle.id,
        position.lat,
        position.lng,
    )
    return {
        "status": "online",
        "driver_id": str(profile.id),
        "vehicle_id": str(vehicle.id),
        "location": {"lat": position.lat, "lng": position.lng},
    }


@router.post("/offline")
async def go_offline(
    locations: RedisDriverLocationService = Depends(get_driver_locations),
    current_user: UserModel = Depends(get_current_active_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    await locations.go_offline(current_user.id)
    logger.info("driver_offline_requested user_id=%s", current_user.id)
    return {"status": "offline"}
