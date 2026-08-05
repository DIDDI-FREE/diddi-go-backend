from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app_base.core.auth_deps import get_current_active_user
from app_base.core.deps import device_service
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.notification.application import DeviceService

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceRegisterRequest(BaseModel):
    platform: str = Field(..., pattern="^(android|ios)$")
    push_token: str = Field(..., min_length=10)
    push_provider: str | None = Field(default=None, pattern="^fcm$")
    device_id: str | None = Field(default=None, max_length=120)


class DeviceUnregisterRequest(BaseModel):
    push_token: str = Field(..., min_length=10)


@router.post("/register")
async def register_device(
    payload: DeviceRegisterRequest,
    current_user: UserModel = Depends(get_current_active_user),
    service: DeviceService = Depends(device_service),
) -> dict:
    return await service.register(
        user_id=current_user.id,
        platform=payload.platform,
        push_token=payload.push_token,
        push_provider=payload.push_provider,
        device_id=payload.device_id,
    )


@router.post("/unregister")
async def unregister_device(
    payload: DeviceUnregisterRequest,
    current_user: UserModel = Depends(get_current_active_user),
    service: DeviceService = Depends(device_service),
) -> dict:
    return await service.unregister(user_id=current_user.id, push_token=payload.push_token)
