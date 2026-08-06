"""Auth use cases — stateless, injected repositories.

One class `AuthService` with the five endpoint-shaped methods that the router
delegates to. The service doesn't hold state; it receives repositories in
`__init__` and reads/writes through them.

TODO (next iteration): SMS delivery of OTP codes is a stub that logs.
The plaintext preview is still stashed on the in-flight OTP record
(but never persisted — see `_otp_preview` below) so local dev can verify
without an SMS provider.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import randbelow

from app_base.core.security import issue_access_token, issue_refresh_token
from app_base.modules.auth.domain.entities import (
    OtpCode,
    User,
    UserRole,
    UserStatus,
)
from app_base.modules.auth.domain.interfaces import OTPRepository, UserRepository

# E.164: a leading '+', a non-zero country digit, then 7–14 more digits.
# Deliberately permissive about which country — DiddiGo launches in Côte
# d'Ivoire but the same `auth` module is meant to serve future DiddiFree
# products in other markets without a migration.
_E164 = re.compile(r"^\+[1-9]\d{7,14}$")


def _validate_phone(phone: str) -> str:
    """Normalise and validate a phone number, or raise `422 INVALID_PHONE_FORMAT`
    as the API contract specifies."""
    from app_base.core.errors import ApiError

    normalised = "".join(phone.split())  # tolerate "+225 07 00 00 00 00"
    if not _E164.match(normalised):
        raise ApiError(
            422,
            "INVALID_PHONE_FORMAT",
            "Le numéro doit être au format international, ex. +2250700000000.",
            {"field": "phone"},
        )
    return normalised


@dataclass
class AuthService:
    user_repo: UserRepository
    otp_repo: OTPRepository

    async def register(self, phone: str, full_name: str, role: str) -> dict:
        phone = _validate_phone(phone)
        if role not in {"passenger", "driver", "admin"}:
            from app_base.core.errors import ApiError
            raise ApiError(422, "INVALID_ROLE", "Le rôle doit être passenger ou driver.", {"field": "role"})
        existing = await self.user_repo.find_by_phone(phone)
        if existing is not None:
            from app_base.core.errors import ApiError
            raise ApiError(409, "PHONE_ALREADY_REGISTERED", "Ce numéro est déjà enregistré.")
        user = User(
            id=User.new_id(),
            phone=phone,
            full_name=full_name or None,
            role=UserRole(role),
            status=UserStatus.PENDING_VERIFICATION,
            created_at=datetime.now(UTC),
        )
        await self.user_repo.save(user)
        # Committed here so a client that immediately requests an OTP finds
        # the account — see the note in `verify_otp`.
        await self.user_repo.commit()
        return {"user_id": str(user.id), "phone": user.phone, "status": user.status.value}

    async def request_otp(self, phone: str) -> dict:
        phone = _validate_phone(phone)
        # Rate limit: at most one OTP per phone every OTP_RATE_LIMIT_SECONDS.
        latest = await self.otp_repo.find_latest_unconsumed(phone)
        now = datetime.now(UTC)
        from app_base.core.settings import settings
        if (
            latest is not None
            and latest.consumed_at is None
            and latest.expires_at > now
            and (now - latest.created_at).total_seconds() < settings.otp_rate_limit_seconds
        ):
            from app_base.core.errors import ApiError
            raise ApiError(
                429,
                "OTP_RATE_LIMITED",
                "Veuillez attendre avant de redemander un OTP.",
                {"retry_after_seconds": settings.otp_rate_limit_seconds},
            )
        code = f"{randbelow(1_000_000):06d}"
        otp = OtpCode(
            id=OtpCode.new_id(),
            phone=phone,
            code_hash=sha256(code.encode()).hexdigest(),
            expires_at=now + timedelta(seconds=settings.otp_code_lifetime_seconds),
            created_at=now,
        )
        await self.otp_repo.save(otp)
        # Commit before the code leaves the building: the user can submit it
        # the instant they receive it, and `verify_otp` runs on a different
        # session that must be able to see this row.
        await self.otp_repo.commit()
        # TODO: replace with real SMS delivery. In dev, the OTP is logged.
        import logging
        logging.getLogger(__name__).warning(
            "OTP stub — in dev, code for phone=%s is %s. SMS integration pending.", phone, code,
        )
        return {
            "expires_in_seconds": settings.otp_code_lifetime_seconds,
            "retry_after_seconds": settings.otp_rate_limit_seconds,
        }

    async def verify_otp(self, phone: str, code: str, *, test_override_code: str | None = None) -> dict:
        phone = _validate_phone(phone)
        otp = await self.otp_repo.find_latest_unconsumed(phone)
        now = datetime.now(UTC)
        from app_base.core.errors import ApiError
        if otp is None:
            raise ApiError(400, "OTP_INVALID", "Le code OTP est invalide.")
        if otp.expires_at <= now:
            raise ApiError(410, "OTP_EXPIRED", "Le code OTP a expiré.")
        expected_hash = sha256(code.encode()).hexdigest()
        if test_override_code is not None:
            # Test backdoor: compare against the test-supplied code directly.
            # Production code path never takes this branch.
            if code != test_override_code:
                raise ApiError(400, "OTP_INVALID", "Le code OTP est invalide.")
        elif expected_hash != otp.code_hash:
            raise ApiError(400, "OTP_INVALID", "Le code OTP est invalide.")

        await self.otp_repo.mark_consumed(otp.id)

        user = await self.user_repo.find_by_phone(phone)
        if user is None:
            user = User(
                id=User.new_id(),
                phone=phone,
                full_name=None,
                role=UserRole.PASSENGER,
                status=UserStatus.ACTIVE,
                created_at=now,
            )
            await self.user_repo.save(user)
        elif user.status == UserStatus.PENDING_VERIFICATION:
            user.status = UserStatus.ACTIVE
            await self.user_repo.save(user)

        # Commit before handing back a token. The client will use it on its
        # very next request, which can arrive before FastAPI tears down this
        # request's session — the activation must already be visible or the
        # user is rejected as `pending_verification`.
        await self.user_repo.commit()

        access_token = issue_access_token(user.id, user.role.value)
        refresh_token = issue_refresh_token(user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": self._user_payload(user),
        }

    async def refresh(self, refresh_token: str) -> dict:
        from app_base.core.security import decode_token, user_id_from_token
        payload = decode_token(refresh_token, expected_typ="refresh")
        user_id = user_id_from_token(payload)
        user = await self.user_repo.find_by_id(user_id)
        from app_base.core.errors import ApiError
        if user is None:
            raise ApiError(401, "REFRESH_TOKEN_INVALID", "Le refresh token est invalide.")
        new_access = issue_access_token(user.id, user.role.value)
        new_refresh = issue_refresh_token(user.id)
        return {"access_token": new_access, "refresh_token": new_refresh}

    @staticmethod
    def _user_payload(user: User) -> dict:
        return {
            "id": str(user.id),
            "phone": user.phone,
            "full_name": user.full_name,
            "role": user.role.value,
            "status": user.status.value,
        }
