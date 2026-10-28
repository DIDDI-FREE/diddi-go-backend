from __future__ import annotations

from fastapi import APIRouter, Depends

from app_base.core.auth_deps import get_current_active_user
from app_base.core.deps import driver_service, emergency_contact_service, scoring_service
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.application.driver_service import DriverService
from app_base.modules.ride.application.emergency_contact_service import EmergencyContactService
from app_base.modules.ride.application.scoring_service import ScoringService
from app_base.modules.ride.presentation.schemas import (
    EmergencyContactUpsertRequest,
    MyScoresResponse,
    ProMetiersResponse,
)

router = APIRouter(prefix="/me", tags=["me"])
pro_router = APIRouter(prefix="/pro", tags=["pro"])


@router.get("/capabilities")
async def get_my_capabilities(
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.get_capabilities(
        current_user.id,
        identity_role=current_user.role,
        identity_status=current_user.status,
    )


@pro_router.get("/metiers", response_model=ProMetiersResponse)
async def get_my_diddigo_metiers(
    service: DriverService = Depends(driver_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    """DiddiGo-local professional projection.

    This endpoint intentionally does not aggregate DiddiSend or any other
    service. DiddiFreeID/DiddiFree Pro remains the future global owner.
    """
    capabilities = await service.get_capabilities(
        current_user.id,
        identity_role=current_user.role,
        identity_status=current_user.status,
    )
    return {
        "scope": "diddigo_local",
        "user_id": str(current_user.id),
        "metiers": capabilities["professional_profiles"],
        "consumer": capabilities["consumer"],
    }


@router.get("/scores", response_model=MyScoresResponse)
async def get_my_scores(
    service: ScoringService = Depends(scoring_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.get_my_scores(current_user.id)


@router.get("/emergency-contact")
async def get_my_emergency_contact(
    service: EmergencyContactService = Depends(emergency_contact_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.get_for_user(current_user.id)


@router.put("/emergency-contact")
async def upsert_my_emergency_contact(
    payload: EmergencyContactUpsertRequest,
    service: EmergencyContactService = Depends(emergency_contact_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.upsert_for_user(
        user_id=current_user.id,
        contact_name=payload.contact_name,
        phone=payload.phone,
        email=payload.email,
        relationship=payload.relationship,
    )


@router.delete("/emergency-contact")
async def delete_my_emergency_contact(
    service: EmergencyContactService = Depends(emergency_contact_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.delete_for_user(current_user.id)
