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
from app_base.core.deps import driver_service, driver_wallet_service, get_driver_locations, partner_service
from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.partner.application.services import PartnerService
from app_base.modules.payment.application.wallet_service import DriverWalletService
from app_base.modules.ride.application.driver_service import DriverService
from app_base.modules.ride.domain.entities import DriverProfile
from app_base.modules.ride.infra.driver_location import RedisDriverLocationService
from app_base.modules.ride.presentation.driver_schemas import (
    DriverKycResubmitRequest,
    DriverKycReviewRequest,
    DriverProfileCreateRequest,
    GoOnlineRequest,
    VehicleCreateRequest,
    VehicleKyvResubmitRequest,
)
from app_base.shared_kernel.types import GeoPoint

router = APIRouter(prefix="/drivers", tags=["driver"])
admin_vehicle_router = APIRouter(prefix="/admin/vehicles", tags=["admin-vehicles"])
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
        license_back_document_file_id=payload.license_back_document_file_id,
        national_id_document_file_id=payload.national_id_document_file_id,
        national_id_back_document_file_id=payload.national_id_back_document_file_id,
        selfie_document_file_id=payload.selfie_document_file_id,
        license_document_url=payload.license_document_url,
        license_back_document_url=payload.license_back_document_url,
        national_id_document_url=payload.national_id_document_url,
        national_id_back_document_url=payload.national_id_back_document_url,
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
        license_back_document_file_id=payload.license_back_document_file_id,
        national_id_document_file_id=payload.national_id_document_file_id,
        national_id_back_document_file_id=payload.national_id_back_document_file_id,
        selfie_document_file_id=payload.selfie_document_file_id,
        license_document_url=payload.license_document_url,
        license_back_document_url=payload.license_back_document_url,
        national_id_document_url=payload.national_id_document_url,
        national_id_back_document_url=payload.national_id_back_document_url,
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
        insurance_document_file_id=payload.insurance_document_file_id,
        technical_inspection_document_file_id=payload.technical_inspection_document_file_id,
        transport_authorization_document_file_id=payload.transport_authorization_document_file_id,
        vehicle_photo_file_id=payload.vehicle_photo_file_id,
        vehicle_front_photo_file_id=payload.vehicle_front_photo_file_id,
        vehicle_back_photo_file_id=payload.vehicle_back_photo_file_id,
        vehicle_left_photo_file_id=payload.vehicle_left_photo_file_id,
        vehicle_right_photo_file_id=payload.vehicle_right_photo_file_id,
        vehicle_interior_photo_file_id=payload.vehicle_interior_photo_file_id,
        registration_document_url=payload.registration_document_url,
        insurance_document_url=payload.insurance_document_url,
        technical_inspection_document_url=payload.technical_inspection_document_url,
        transport_authorization_document_url=payload.transport_authorization_document_url,
        vehicle_photo_url=payload.vehicle_photo_url,
        vehicle_front_photo_url=payload.vehicle_front_photo_url,
        vehicle_back_photo_url=payload.vehicle_back_photo_url,
        vehicle_left_photo_url=payload.vehicle_left_photo_url,
        vehicle_right_photo_url=payload.vehicle_right_photo_url,
        vehicle_interior_photo_url=payload.vehicle_interior_photo_url,
    )


@router.post("/vehicles/{vehicle_id}/kyv/resubmit")
async def resubmit_vehicle_kyv(
    vehicle_id: UUID,
    payload: VehicleKyvResubmitRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(get_current_active_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    return await service.resubmit_vehicle_kyv(
        vehicle_id,
        user_id=current_user.id,
        **payload.model_dump(exclude_unset=True),
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


@router.post("/vehicles/{vehicle_id}/kyv/approve")
async def approve_vehicle_kyv(
    vehicle_id: UUID,
    payload: DriverKycReviewRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.approve_vehicle_kyv(vehicle_id, reviewed_by_user_id=current_user.id, notes=payload.notes)


@router.post("/vehicles/{vehicle_id}/kyv/reject")
async def reject_vehicle_kyv(
    vehicle_id: UUID,
    payload: DriverKycReviewRequest,
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.reject_vehicle_kyv(vehicle_id, reviewed_by_user_id=current_user.id, notes=payload.notes)


@admin_vehicle_router.get("/kyv")
async def list_vehicle_kyv_queue(
    status: str = Query(default="pending_verification"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: DriverService = Depends(driver_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.list_vehicle_kyv_queue(status=status, page=page, page_size=page_size)


@admin_vehicle_router.get("/{vehicle_id}/kyv")
async def get_vehicle_kyv_detail(
    vehicle_id: UUID,
    service: DriverService = Depends(driver_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.get_vehicle_kyv_detail(vehicle_id)


@router.post("/online")
async def go_online(
    payload: GoOnlineRequest,
    service: DriverService = Depends(driver_service),
    wallets: DriverWalletService = Depends(driver_wallet_service),
    partners: PartnerService = Depends(partner_service),
    locations: RedisDriverLocationService = Depends(get_driver_locations),
    current_user: UserModel = Depends(get_current_active_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    """Enter the matching pool. Rejected unless the driver is verified and
    has an active vehicle — matching must never offer a ride to a driver who
    cannot legally take it."""
    profile, vehicle = await service.resolve_driver(current_user.id)
    blocked, reason = await partners.driver_is_blocked_by_partner(profile.id)
    if blocked:
        log_event(
            "driver.online.blocked",
            level="warning",
            driver_id=profile.id,
            user_id=current_user.id,
            reason=reason,
        )
        raise ApiError(
            403,
            ErrorCode.PARTNER_SUSPENDED,
            "Votre partenaire n'est pas actif. Vous ne pouvez pas passer en ligne.",
            {"reason": reason},
        )
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
    log_event(
        "driver.online",
        user_id=current_user.id,
        driver_id=profile.id,
        vehicle_id=vehicle.id,
        lat=position.lat,
        lng=position.lng,
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
    log_event("driver.offline", user_id=current_user.id)
    return {"status": "offline"}
