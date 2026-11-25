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
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError

from app_base.core.errors import ApiError
from app_base.core.service_scopes import canonicalize_scopes
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
            raise ApiError(401, "TOKEN_EXPIRED", "Le token a expire.") from exc
        except jwt.InvalidTokenError as exc:
            raise ApiError(401, "TOKEN_INVALID", f"Token invalide: {exc}") from exc

        if payload.get("status") != "active":
            raise ApiError(403, "USER_NOT_VERIFIED", "Compte non actif.")
        return payload

    def decode_service_token(
        self,
        token: str,
        *,
        audience: str,
        required_scopes: set[str] | frozenset[str] = frozenset(),
        client_id: str | None = None,
        expected_subject: str | None = None,
    ) -> dict:
        """Verify a DiddiFreeID client-credentials token for this service."""
        try:
            signing_key = self._client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self._issuer,
                audience=audience,
                options={
                    "require": ["exp", "iat", "sub", "iss", "aud", "scope", "token_type"],
                },
            )
        except PyJWKClientConnectionError as exc:
            raise ApiError(
                503, "SERVICE_JWKS_UNAVAILABLE", "Cles de verification temporairement indisponibles."
            ) from exc
        except PyJWKClientError as exc:
            raise ApiError(401, "SERVICE_TOKEN_INVALID", "Cle de signature du token service inconnue.") from exc
        except jwt.ExpiredSignatureError as exc:
            raise ApiError(401, "SERVICE_TOKEN_EXPIRED", "Le token service a expire.") from exc
        except jwt.InvalidTokenError as exc:
            raise ApiError(401, "SERVICE_TOKEN_INVALID", f"Token service invalide: {exc}") from exc

        if payload.get("role") != "service" or payload.get("token_type") != "service":
            raise ApiError(401, "SERVICE_TOKEN_INVALID", "Le token n'est pas un token service.")
        if expected_subject is not None and payload.get("sub") != expected_subject:
            raise ApiError(403, "SERVICE_SUBJECT_INVALID", "Service appelant non autorisé.")
        if payload.get("status") != "active":
            raise ApiError(403, "SERVICE_TOKEN_INACTIVE", "Le client service n'est pas actif.")
        if client_id is not None and payload.get("client_id") != client_id:
            raise ApiError(401, "SERVICE_CLIENT_ID_INVALID", "X-Client-ID ne correspond pas au token.")

        token_scopes = canonicalize_scopes(set(str(payload.get("scope", "")).split()))
        if not required_scopes.issubset(token_scopes):
            raise ApiError(403, "SERVICE_SCOPE_INVALID", "Scopes insuffisants pour cette opération.")
        return payload


def identity_mode_enabled() -> bool:
    return bool(settings.effective_identity_jwks_url)


def decode_identity_access_token(token: str) -> dict:
    jwks_url = settings.effective_identity_jwks_url
    if not jwks_url:
        raise ApiError(500, "IDENTITY_NOT_CONFIGURED", "DiddiFreeID n'est pas configure.")
    return IdentityTokenVerifier(jwks_url, settings.identity_issuer).decode_access_token(token)


def decode_identity_service_token(
    token: str,
    *,
    audience: str,
    required_scopes: set[str] | frozenset[str] = frozenset(),
    client_id: str | None = None,
    expected_subject: str | None = None,
) -> dict:
    jwks_url = settings.effective_identity_jwks_url
    if not jwks_url:
        raise ApiError(500, "IDENTITY_NOT_CONFIGURED", "DiddiFreeID n'est pas configure.")
    return IdentityTokenVerifier(jwks_url, settings.identity_issuer).decode_service_token(
        token,
        audience=audience,
        required_scopes=required_scopes,
        client_id=client_id,
        expected_subject=expected_subject,
    )


def user_id_from_identity_payload(payload: dict) -> UUID:
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise ApiError(401, "TOKEN_INVALID", "Claim `sub` manquant ou malforme.")
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
    review_flag = payload.get("is_review_account", False)
    if not isinstance(review_flag, bool):
        raise ApiError(401, "TOKEN_INVALID", "Claim `is_review_account` invalide.")
    user.is_review_account = review_flag
    user.requested_role = data.get("requested_role")
    # Account creation date from DiddiFreeID (ticket 046). Only used when DiddiGo creates its
    # local copy of the user; a problem is kept here and raised only for a new user.
    user.created_at, user.identity_created_at_problem = _profile_created_at(profile)
    # DiddiGo's own "last changed" time, not a DiddiFreeID field.
    user.updated_at = datetime.now(UTC)
    return user


def _profile_created_at(profile: dict | None) -> tuple[datetime | None, dict | None]:
    """Read `created_at` of a DiddiFreeID profile. Returns (date, None) or (None, problem).

    The problem says exactly what is wrong, for the error answer and the logs.
    """
    if profile is None:
        return None, {
            "problem": "profile_missing",
            "message": (
                "DiddiFreeID n'a renvoye aucun profil pour cet utilisateur (reponse 404, ou URL du profil "
                "non configuree dans DiddiGo). DiddiGo ne peut pas creer le compte sans la date de creation "
                "du compte DiddiFreeID (champ created_at)."
            ),
        }
    if "created_at" not in profile or profile.get("created_at") is None:
        return None, {
            "problem": "missing",
            "message": (
                "Le profil DiddiFreeID ne contient pas le champ created_at (date de creation du compte), "
                "ou il vaut null. DiddiGo ne peut pas creer le compte sans cette date."
            ),
        }
    value = profile["created_at"]
    if not isinstance(value, str):
        return None, {
            "problem": "unreadable",
            "received": repr(value)[:80],
            "message": (
                f"Le champ created_at du profil DiddiFreeID n'est pas un texte de date mais {type(value).__name__} "
                f"({repr(value)[:80]}). Attendu : une date ISO 8601 en UTC, par exemple 2026-09-21T13:00:00Z."
            ),
        }
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is None or parsed.tzinfo is None:
        reason = "n'est pas une date ISO 8601 lisible" if parsed is None else "n'a pas de fuseau horaire"
        return None, {
            "problem": "unreadable",
            "received": value[:80],
            "message": (
                f"Le champ created_at du profil DiddiFreeID vaut '{value[:80]}', qui {reason}. "
                "Attendu : une date ISO 8601 en UTC, par exemple 2026-09-21T13:00:00Z."
            ),
        }
    return parsed.astimezone(UTC), None
