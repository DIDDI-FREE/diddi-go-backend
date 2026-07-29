"""Auth router — `/v1/auth/*` endpoints per API contract §1.

Note: handlers are `async def` because the underlying `AuthService` uses
async repository methods. FastAPI awaits each handler automatically.

`/auth/me` uses the `get_current_user` dependency so the response is
derived from the access token, not from a server-side dict lookup.
"""

from fastapi import APIRouter, Depends

from app_base.core.auth_deps import get_current_user
from app_base.core.deps import auth_service
from app_base.modules.auth.application.services import AuthService
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.auth.presentation.schemas import (
    OTPRequest,
    OTPVerifyRequest,
    RefreshRequest,
    RegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(payload: RegisterRequest, service: AuthService = Depends(auth_service)) -> dict:
    return await service.register(payload.phone, payload.full_name, payload.role)


@router.post("/otp/request")
async def request_otp(payload: OTPRequest, service: AuthService = Depends(auth_service)) -> dict:
    return await service.request_otp(payload.phone)


@router.post("/otp/verify")
async def verify_otp(payload: OTPVerifyRequest, service: AuthService = Depends(auth_service)) -> dict:
    return await service.verify_otp(payload.phone, payload.code)


@router.post("/refresh")
async def refresh(payload: RefreshRequest, service: AuthService = Depends(auth_service)) -> dict:
    return await service.refresh(payload.refresh_token)


@router.get("/me")
async def me(current_user: UserModel = Depends(get_current_user)) -> dict:
    return {
        "id": str(current_user.id),
        "phone": current_user.phone,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "status": current_user.status,
    }
