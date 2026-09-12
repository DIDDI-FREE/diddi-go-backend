from __future__ import annotations

from fastapi import APIRouter, Depends

from app_base.core.auth_deps import get_current_active_user
from app_base.core.deps import driver_service
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.application.driver_service import DriverService

router = APIRouter(prefix="/me", tags=["me"])


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
