"""Driver router — `/v1/drivers/*`.

Onboarding (profile + vehicle) and availability (go online / offline).
Every route is driver-only: a passenger token gets `403 FORBIDDEN_ROLE`.

These endpoints are the prerequisite for matching — a ride can only be
assigned to a driver who has a verified profile, an active vehicle, and a
live position in the Redis pool.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app_base.core.auth_deps import get_current_active_user, require_business_driver, require_role
from app_base.core.deps import driver_service, driver_wallet_service, get_driver_locations
from app_base.modules.payment.application.wallet_service import DriverWalletService
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.application.driver_service import DriverService
from app_base.modules.ride.domain.entities import DriverProfile
from app_base.modules.ride.infra.driver_location import RedisDriverLocationService
from app_base.modules.ride.presentation.driver_schemas import (
    DriverKycResubmitRequest,
    DriverKycReviewRequest,
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


@router.post("/kyc/resubmit")
async def resubmit_kyc(
    payload: DriverKycResubmitRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.resubmit_kyc(
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


@router.get("/kyc")
async def list_driver_kyc_queue(
    status: str = Query(default="pending_verification"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: DriverService = Depends(driver_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.list_kyc_queue(status=status, page=page, page_size=page_size)


@router.get("/{driver_id}/kyc")
async def get_driver_kyc_detail(
    driver_id: UUID,
    service: DriverService = Depends(driver_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.get_kyc_detail(driver_id)


@router.post("/{driver_id}/kyc/approve")
async def approve_driver_kyc(
    driver_id: UUID,
    payload: DriverKycReviewRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.approve_kyc(
        driver_id,
        reviewed_by_user_id=current_user.id,
        notes=payload.notes,
    )


@router.post("/{driver_id}/kyc/reject")
async def reject_driver_kyc(
    driver_id: UUID,
    payload: DriverKycReviewRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.reject_kyc(
        driver_id,
        reviewed_by_user_id=current_user.id,
        notes=payload.notes,
    )


@router.post("/online")
async def go_online(
    payload: GoOnlineRequest,
    service: DriverService = Depends(driver_service),
    wallets: DriverWalletService = Depends(driver_wallet_service),
    locations: RedisDriverLocationService = Depends(get_driver_locations),
    current_user: UserModel = Depends(get_current_active_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    """Enter the matching pool. Rejected unless the driver is verified and
    has an active vehicle — matching must never offer a ride to a driver who
    cannot legally take it."""
    profile, vehicle = await service.resolve_driver(current_user.id)
    await wallets.ensure_driver_can_go_online(profile.id)
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
