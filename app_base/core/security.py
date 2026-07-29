"""JWT issuance/verification — fast, stateless tokens for access + refresh.

Per the API contract (`DiddiGo_Contrat_API.md` §0):
  - access_token: TTL = JWT_ACCESS_LIFETIME_MINUTES (default 15 min)
  - refresh_token: TTL = JWT_REFRESH_LIFETIME_DAYS (default 30 days),
    only valid on /auth/refresh — distinguished by `typ=refresh` claim

Token payload: `{ sub: user_id (UUID), role: str, exp, iat, typ? }`.

Signing algorithm: HS256 with `settings.jwt_secret`. Simple, symmetric,
sufficient for an in-process monolith. RS256 can replace this later if
we need to hand token verification to an external service without
sharing the secret.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app_base.core.errors import ApiError
from app_base.core.settings import settings

ACCESS_TOKEN_TYP = "access"
REFRESH_TOKEN_TYP = "refresh"
ALGORITHM = "HS256"


def issue_access_token(user_id: UUID, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "typ": ACCESS_TOKEN_TYP,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_lifetime_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def issue_refresh_token(user_id: UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "typ": REFRESH_TOKEN_TYP,
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_refresh_lifetime_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str, *, expected_typ: str = ACCESS_TOKEN_TYP) -> dict:
    """Decode and validate a token. Raises `ApiError` with the contract-
    mandated error codes:
      - `TOKEN_EXPIRED` on exp failure
      - `TOKEN_INVALID` on everything else (malformed, wrong typ, bad sig).
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "typ"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise ApiError(401, "TOKEN_EXPIRED", "Le token a expiré.") from exc
    except jwt.InvalidTokenError as exc:
        raise ApiError(401, "TOKEN_INVALID", f"Token invalide: {exc}") from exc

    if payload.get("typ") != expected_typ:
        raise ApiError(401, "TOKEN_INVALID", "Type de token non attendu.")
    return payload


def user_id_from_token(payload: dict) -> UUID:
    """Helper — extract UUID-shaped `sub` claim or raise."""
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise ApiError(401, "TOKEN_INVALID", "Claim `sub` manquant ou malformé.")
    try:
        return UUID(sub)
    except ValueError as exc:
        raise ApiError(401, "TOKEN_INVALID", f"Claim `sub` invalide: {exc}") from exc
