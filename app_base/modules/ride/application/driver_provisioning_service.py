"""Backoffice-first provisioning of a DiddiGo driver business profile."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.modules.auth.domain.entities import User, UserRole, UserStatus
from app_base.modules.auth.domain.interfaces import UserRepository
from app_base.modules.ride.application.driver_service import DriverService


@dataclass
class DriverProvisioningService:
    users: UserRepository
    drivers: DriverService

    async def provision(
        self,
        *,
        user_id: UUID,
        full_name: str | None,
        profile_fields: dict[str, Any],
    ) -> dict[str, Any]:
        user = await self.users.find_by_id(user_id)
        if user is not None and user.status != UserStatus.ACTIVE:
            raise ApiError(403, ErrorCode.USER_SUSPENDED, "L'identite cible n'est pas active.")

        existing = await self.drivers.driver_repo.find_by_user_id(user_id)
        if existing is not None:
            profile = await self.drivers.get_profile(user_id)
            if not _matches_requested_profile(profile, profile_fields):
                raise ApiError(
                    409,
                    ErrorCode.DRIVER_PROVISIONING_CONFLICT,
                    "Un profil chauffeur different existe deja pour cette identite.",
                )
            return {"created": False, "profile": profile}

        if user is None:
            await self.users.save(
                User(
                    id=user_id,
                    phone=_shadow_phone(user_id),
                    full_name=full_name,
                    role=UserRole.PASSENGER,
                    status=UserStatus.ACTIVE,
                ),
            )

        profile = await self.drivers.create_profile(user_id=user_id, **profile_fields)
        # The shadow user and profile share the request session; commit both
        # before returning so a following Backoffice request sees the result.
        await self.users.commit()
        log_event("driver.profile.s2s_provisioned", driver_id=profile["id"], user_id=user_id)
        return {"created": True, "profile": profile}


def _matches_requested_profile(profile: dict[str, Any], requested: dict[str, Any]) -> bool:
    kyc = profile.get("kyc", {})
    current = {
        "license_number": profile.get("license_number"),
        "legal_name": kyc.get("legal_name"),
        "birth_date": kyc.get("birth_date"),
        "residence_address": kyc.get("residence_address"),
        "license_document_file_id": kyc.get("license_document_file_id"),
        "license_back_document_file_id": kyc.get("license_back_document_file_id"),
        "national_id_document_file_id": kyc.get("national_id_document_file_id"),
        "national_id_back_document_file_id": kyc.get("national_id_back_document_file_id"),
        "selfie_document_file_id": kyc.get("selfie_document_file_id"),
        "license_document_url": kyc.get("license_document_url"),
        "license_back_document_url": kyc.get("license_back_document_url"),
        "national_id_document_url": kyc.get("national_id_document_url"),
        "national_id_back_document_url": kyc.get("national_id_back_document_url"),
        "selfie_document_url": kyc.get("selfie_document_url"),
    }
    normalized_requested = {
        key: value.isoformat() if hasattr(value, "isoformat") else str(value) if isinstance(value, UUID) else value
        for key, value in requested.items()
    }
    return current == normalized_requested


def _shadow_phone(user_id: UUID) -> str:
    return f"+000{user_id.int % 1_000_000_000_000:012d}"
