"""FastAPI dependencies for authentication.

`get_current_user` is the universal protected-route dependency. Routers declare:
    `current_user: UserModel = Depends(get_current_user)`
and the framework resolves:
  1. Bearer token from the `Authorization` header (via `oauth2_scheme`)
  2. Decodes it → `sub` user_id + `typ=access`
  3. Loads the User from the DB via `UserRepository`
  4. Returns the SQLAlchemy row (not the domain entity) — the row is what the
     service layer passes into the response builder.

Two convenience deps for role gating:
    `get_current_active_user` — rejects suspended users
    `require_role(*roles)`     — returns a dep that asserts role
"""

from __future__ import annotations

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from app_base.core.deps import driver_profile_repo, user_repo
from app_base.core.errors import ApiError
from app_base.core.identity import (
    decode_identity_access_token,
    fetch_identity_profile,
    identity_mode_enabled,
    identity_payload_to_user_model,
)
from app_base.core.security import decode_token, user_id_from_token
from app_base.modules.auth.domain.entities import User, UserRole, UserStatus
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.auth.infra.repositories import SqlAlchemyUserRepository
from app_base.modules.ride.infra.repositories import SqlAlchemyDriverProfileRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/otp/verify", auto_error=False)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    repo: SqlAlchemyUserRepository = Depends(user_repo),
) -> UserModel:
    if not token:
        raise ApiError(401, "TOKEN_MISSING", "Authentification requise.")
    if identity_mode_enabled():
        payload = decode_identity_access_token(token)
        profile = await fetch_identity_profile(token)
        user = identity_payload_to_user_model(payload, profile)
        await _upsert_identity_shadow_user(user, repo)
        request.state.current_user = user
        return user

    payload = decode_token(token, expected_typ="access")  # 401 TOKEN_EXPIRED / TOKEN_INVALID
    user_id = user_id_from_token(payload)
    user = await repo.find_by_id(user_id)
    if user is None:
        raise ApiError(401, "TOKEN_INVALID", "Utilisateur introuvable.")
    if user.status != "active":
        raise ApiError(403, "USER_SUSPENDED", "Compte suspendu.")
    request.state.current_user = user
    return user


async def get_current_active_user(
    user: UserModel = Depends(get_current_user),
) -> UserModel:
    if user.status != "active":
        raise ApiError(403, "USER_SUSPENDED", "Compte suspendu.")
    return user


def require_role(*roles: str):
    """Factory returning a dependency that enforces the current user's role.

    Usage:
        @router.get("/admin-only")
        def admin_only(me: UserModel = Depends(require_role("admin"))): ...
    """
    async def _dep(user: UserModel = Depends(get_current_active_user)) -> UserModel:
        if user.role not in roles:
            raise ApiError(403, "FORBIDDEN_ROLE", "Rôle insuffisant pour cette action.")
        return user
    return _dep


async def require_business_driver(
    user: UserModel = Depends(get_current_active_user),
    driver_repo: SqlAlchemyDriverProfileRepository = Depends(driver_profile_repo),
):
    """Allow a DiddiAuth `user` to act as a DiddiGo driver only after a local
    driver profile exists and is active. Admins bypass this gate."""
    if user.role == "admin":
        return None

    profile = await driver_repo.find_by_user_id(user.id)
    if profile is None:
        raise ApiError(404, "DRIVER_PROFILE_NOT_FOUND", "Aucun profil chauffeur pour ce compte.")
    if profile.status.value != "active":
        raise ApiError(
            403,
            "DRIVER_NOT_VERIFIED",
            "Votre profil chauffeur n'est pas encore validÃ©.",
            {"status": profile.status.value},
        )
    return profile


async def _upsert_identity_shadow_user(user: UserModel, repo: SqlAlchemyUserRepository) -> None:
    shadow = User(
        id=user.id,
        phone=user.phone or _shadow_phone(user.id),
        full_name=user.full_name,
        role=UserRole.ADMIN if user.role == "admin" else UserRole.PASSENGER,
        status=UserStatus.ACTIVE if user.status == "active" else UserStatus.SUSPENDED,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
    await repo.save(shadow)
    await repo.commit()


def _shadow_phone(user_id) -> str:
    return f"+000{user_id.int % 1_000_000_000_000:012d}"
