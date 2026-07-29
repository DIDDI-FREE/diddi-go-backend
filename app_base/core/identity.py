"""DiddiFreeID token verification.

Ride/DiddiGo consumes identity tokens locally: it validates RS256 JWTs from
DiddiFreeID using the JWKS endpoint, without calling Identity on every request.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import httpx
import jwt
from jwt import PyJWKClient

from app_base.core.errors import ApiError
from app_base.core.settings import settings


class IdentityTokenVerifier:
    def __init__(self, jwks_url: str, issuer: str) -> None:
        self._jwks_url = jwks_url
        self._issuer = issuer
        self._client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)

    def decode_access_token(self, token: str) -> dict:
        try:
            signing_key = self._client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self._issuer,
                options={"require": ["exp", "sub", "iss"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise ApiError(401, "TOKEN_EXPIRED", "Le token a expiré.") from exc
        except jwt.InvalidTokenError as exc:
            raise ApiError(401, "TOKEN_INVALID", f"Token invalide: {exc}") from exc

        if payload.get("status") != "active":
            raise ApiError(403, "USER_NOT_VERIFIED", "Compte non actif.")
        return payload


def identity_mode_enabled() -> bool:
    return bool(settings.effective_identity_jwks_url)


def decode_identity_access_token(token: str) -> dict:
    jwks_url = settings.effective_identity_jwks_url
    if not jwks_url:
        raise ApiError(500, "IDENTITY_NOT_CONFIGURED", "DiddiFreeID n'est pas configuré.")
    return IdentityTokenVerifier(jwks_url, settings.identity_issuer).decode_access_token(token)


def user_id_from_identity_payload(payload: dict) -> UUID:
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise ApiError(401, "TOKEN_INVALID", "Claim `sub` manquant ou malformé.")
    try:
        return UUID(sub)
    except ValueError as exc:
        raise ApiError(401, "TOKEN_INVALID", f"Claim `sub` invalide: {exc}") from exc


async def fetch_identity_profile(token: str) -> dict | None:
    profile_url = settings.effective_identity_profile_url
    if not profile_url:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    if settings.identity_service_key:
        headers["X-Service-Key"] = settings.identity_service_key
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.get(profile_url, headers=headers)
    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise ApiError(response.status_code, "IDENTITY_PROFILE_ERROR", "Profil DiddiFreeID indisponible.")
    return response.json()


def identity_payload_to_user_model(payload: dict, profile: dict | None = None):
    from app_base.modules.auth.infra.models import UserModel

    data = profile or {}
    user = UserModel()
    user.id = user_id_from_identity_payload(payload)
    user.phone = data.get("phone") or ""
    user.full_name = data.get("full_name")
    role = payload.get("role") or data.get("role") or "user"
    user.role = "passenger" if role == "user" else role
    user.status = payload.get("status") or data.get("status") or "active"
    now = datetime.now(UTC)
    user.created_at = data.get("created_at") or now
    user.updated_at = data.get("updated_at") or now
    return user
