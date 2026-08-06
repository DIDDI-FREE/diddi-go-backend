"""Driver onboarding use cases.

A `driver` user in `auth.users` is not yet a driver who can take rides: they
need a `ride.driver_profiles` row (licence, KYC status) and at least one
active `ride.vehicles` row. This service owns that onboarding path.

KYC note: `license_verified_at` is left NULL and `status` starts at
`pending_verification`. Only an admin KYC review may activate the driver.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    DriverProfile,
    DriverStatus,
    Vehicle,
    VehicleCategory,
)
from app_base.modules.ride.domain.interfaces import (
    DriverProfileRepository,
    VehicleRepository,
)


@dataclass
class DriverService:
    driver_repo: DriverProfileRepository
    vehicle_repo: VehicleRepository

    async def create_profile(
        self,
        *,
        user_id: UUID,
        license_number: str,
        legal_name: str | None = None,
        birth_date: date | None = None,
        residence_address: str | None = None,
        license_document_file_id: UUID | None = None,
        national_id_document_file_id: UUID | None = None,
        selfie_document_file_id: UUID | None = None,
        license_document_url: str | None = None,
        national_id_document_url: str | None = None,
        selfie_document_url: str | None = None,
    ) -> dict:
        if not license_number or not license_number.strip():
            raise ApiError(
                422, "INVALID_LICENSE_NUMBER", "Le numéro de permis est obligatoire.",
                {"field": "license_number"},
            )

        existing = await self.driver_repo.find_by_user_id(user_id)
        if existing is not None:
            raise ApiError(
                409, "DRIVER_PROFILE_ALREADY_EXISTS", "Ce compte a déjà un profil chauffeur.",
            )

        now = datetime.now(UTC)
        profile = DriverProfile(
            id=DriverProfile.new_id(),
            user_id=user_id,
            license_number=license_number.strip(),
            status=DriverStatus.PENDING_VERIFICATION,
            license_verified_at=None,
            legal_name=_blank_to_none(legal_name),
            birth_date=birth_date,
            residence_address=_blank_to_none(residence_address),
            license_document_file_id=license_document_file_id,
            national_id_document_file_id=national_id_document_file_id,
            selfie_document_file_id=selfie_document_file_id,
            license_document_url=_blank_to_none(license_document_url),
            national_id_document_url=_blank_to_none(national_id_document_url),
            selfie_document_url=_blank_to_none(selfie_document_url),
            kyc_submitted_at=now,
            created_at=now,
            updated_at=now,
        )
        await self.driver_repo.save(profile)
        return _profile_payload(profile)

    async def resubmit_kyc(
        self,
        *,
        user_id: UUID,
        license_number: str | None = None,
        legal_name: str | None = None,
        birth_date: date | None = None,
        residence_address: str | None = None,
        license_document_file_id: UUID | None = None,
        national_id_document_file_id: UUID | None = None,
        selfie_document_file_id: UUID | None = None,
        license_document_url: str | None = None,
        national_id_document_url: str | None = None,
        selfie_document_url: str | None = None,
    ) -> dict:
        profile = await self._require_profile(user_id)
        if license_number is not None:
            if not license_number.strip():
                raise ApiError(
                    422,
                    ErrorCode.INVALID_LICENSE_NUMBER,
                    "Le numero de permis est obligatoire.",
                    {"field": "license_number"},
                )
            profile.license_number = license_number.strip()

        _update_optional_kyc_fields(
            profile,
            legal_name=legal_name,
            birth_date=birth_date,
            residence_address=residence_address,
            license_document_file_id=license_document_file_id,
            national_id_document_file_id=national_id_document_file_id,
            selfie_document_file_id=selfie_document_file_id,
            license_document_url=license_document_url,
            national_id_document_url=national_id_document_url,
            selfie_document_url=selfie_document_url,
        )
        now = datetime.now(UTC)
        profile.status = DriverStatus.PENDING_VERIFICATION
        profile.license_verified_at = None
        profile.kyc_submitted_at = now
        profile.kyc_reviewed_at = None
        profile.kyc_review_notes = None
        profile.updated_at = now
        await self.driver_repo.save(profile)
        return _profile_payload(profile)

    async def approve_kyc(self, driver_id: UUID, *, reviewed_by_user_id: UUID, notes: str | None = None) -> dict:
        profile = await self.driver_repo.find_by_id(driver_id)
        if profile is None:
            raise ApiError(404, "DRIVER_PROFILE_NOT_FOUND", "Aucun profil chauffeur pour cet identifiant.")
        now = datetime.now(UTC)
        profile.status = DriverStatus.ACTIVE
        profile.license_verified_at = now
        profile.kyc_reviewed_at = now
        profile.kyc_review_notes = _review_note(notes, reviewed_by_user_id)
        profile.updated_at = now
        await self.driver_repo.save(profile)
        return _profile_payload(profile)

    async def reject_kyc(self, driver_id: UUID, *, reviewed_by_user_id: UUID, notes: str | None = None) -> dict:
        profile = await self.driver_repo.find_by_id(driver_id)
        if profile is None:
            raise ApiError(404, "DRIVER_PROFILE_NOT_FOUND", "Aucun profil chauffeur pour cet identifiant.")
        now = datetime.now(UTC)
        profile.status = DriverStatus.SUSPENDED
        profile.license_verified_at = None
        profile.kyc_reviewed_at = now
        profile.kyc_review_notes = _review_note(notes, reviewed_by_user_id)
        profile.updated_at = now
        await self.driver_repo.save(profile)
        return _profile_payload(profile)

    async def register_vehicle(
        self,
        *,
        user_id: UUID,
        plate_number: str,
        make: str | None,
        model: str | None,
        color: str | None,
        category: str,
        comfort_level: str = "standard",
        registration_document_file_id: UUID | None = None,
    ) -> dict:
        if category not in {c.value for c in VehicleCategory}:
            raise ApiError(
                422, "INVALID_VEHICLE_CATEGORY", "Catégorie de véhicule invalide.",
                {"field": "category"},
            )
        if comfort_level not in {c.value for c in ComfortLevel}:
            raise ApiError(
                422, "INVALID_COMFORT_LEVEL", "Niveau de confort invalide.",
                {"field": "comfort_level"},
            )
        profile = await self._require_profile(user_id)

        vehicle = Vehicle(
            id=Vehicle.new_id(),
            driver_id=profile.id,
            plate_number=plate_number.strip().upper(),
            make=make,
            model=model,
            color=color,
            registration_document_file_id=registration_document_file_id,
            category=VehicleCategory(category),
            comfort_level=ComfortLevel(comfort_level),
            active=True,
            created_at=datetime.now(UTC),
        )
        try:
            await self.vehicle_repo.save(vehicle)
        except Exception as exc:  # unique violation on plate_number
            if "plate_number" in str(exc):
                raise ApiError(
                    409, "PLATE_ALREADY_REGISTERED", "Cette plaque est déjà enregistrée.",
                ) from exc
            raise
        return _vehicle_payload(vehicle)

    async def get_profile(self, user_id: UUID) -> dict:
        profile = await self._require_profile(user_id)
        vehicle = await self.vehicle_repo.find_active_for_driver(profile.id)
        payload = _profile_payload(profile)
        payload["vehicle"] = _vehicle_payload(vehicle) if vehicle else None
        return payload

    async def get_kyc_detail(self, driver_id: UUID) -> dict:
        profile = await self.driver_repo.find_by_id(driver_id)
        if profile is None:
            raise ApiError(404, ErrorCode.DRIVER_PROFILE_NOT_FOUND, "Aucun profil chauffeur pour cet identifiant.")
        vehicle = await self.vehicle_repo.find_active_for_driver(profile.id)
        payload = _profile_payload(profile)
        payload["vehicle"] = _vehicle_payload(vehicle) if vehicle else None
        return payload

    async def list_kyc_queue(
        self,
        *,
        status: str = "pending_verification",
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        if status == "all":
            statuses = [
                DriverStatus.PENDING_VERIFICATION,
                DriverStatus.ACTIVE,
                DriverStatus.SUSPENDED,
            ]
        else:
            try:
                statuses = [DriverStatus(status)]
            except ValueError as exc:
                raise ApiError(
                    422,
                    ErrorCode.DRIVER_KYC_STATUS_INVALID,
                    "Statut KYC chauffeur invalide.",
                    {"field": "status", "allowed": ["pending_verification", "active", "suspended", "all"]},
                ) from exc
        profiles, total = await self.driver_repo.list_by_status(statuses, page=page, page_size=page_size)
        return {
            "data": [_profile_payload(profile) for profile in profiles],
            "pagination": {"page": page, "page_size": page_size, "total": total},
        }

    async def resolve_driver(self, user_id: UUID) -> tuple[DriverProfile, Vehicle]:
        """Profile + active vehicle for a driver about to go online or take a
        ride. Raises if either is missing — matching must never hand a ride to
        a driver with no vehicle on file."""
        profile = await self._require_profile(user_id)
        if profile.status != DriverStatus.ACTIVE:
            raise ApiError(
                403,
                "DRIVER_NOT_VERIFIED",
                "Votre profil chauffeur n'est pas encore validé.",
                {"status": profile.status.value},
            )
        vehicle = await self.vehicle_repo.find_active_for_driver(profile.id)
        if vehicle is None:
            raise ApiError(
                409, "NO_ACTIVE_VEHICLE", "Aucun véhicule actif n'est associé à ce chauffeur.",
            )
        return profile, vehicle

    async def _require_profile(self, user_id: UUID) -> DriverProfile:
        profile = await self.driver_repo.find_by_user_id(user_id)
        if profile is None:
            raise ApiError(
                404, "DRIVER_PROFILE_NOT_FOUND", "Aucun profil chauffeur pour ce compte.",
            )
        return profile


def _profile_payload(profile: DriverProfile) -> dict:
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "license_number": profile.license_number,
        "status": profile.status.value,
        "rating_avg": float(profile.rating_avg) if profile.rating_avg is not None else None,
        "rating_count": profile.rating_count,
        "kyc": {
            "legal_name": profile.legal_name,
            "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
            "residence_address": profile.residence_address,
            "license_document_file_id": str(profile.license_document_file_id)
            if profile.license_document_file_id
            else None,
            "national_id_document_file_id": str(profile.national_id_document_file_id)
            if profile.national_id_document_file_id
            else None,
            "selfie_document_file_id": str(profile.selfie_document_file_id)
            if profile.selfie_document_file_id
            else None,
            "license_document_url": profile.license_document_url,
            "national_id_document_url": profile.national_id_document_url,
            "selfie_document_url": profile.selfie_document_url,
            "submitted_at": profile.kyc_submitted_at.isoformat() if profile.kyc_submitted_at else None,
            "reviewed_at": profile.kyc_reviewed_at.isoformat() if profile.kyc_reviewed_at else None,
            "review_notes": profile.kyc_review_notes,
        },
    }


def _update_optional_kyc_fields(
    profile: DriverProfile,
    *,
    legal_name: str | None,
    birth_date: date | None,
    residence_address: str | None,
    license_document_file_id: UUID | None,
    national_id_document_file_id: UUID | None,
    selfie_document_file_id: UUID | None,
    license_document_url: str | None,
    national_id_document_url: str | None,
    selfie_document_url: str | None,
) -> None:
    if legal_name is not None:
        profile.legal_name = _blank_to_none(legal_name)
    if birth_date is not None:
        profile.birth_date = birth_date
    if residence_address is not None:
        profile.residence_address = _blank_to_none(residence_address)
    if license_document_file_id is not None:
        profile.license_document_file_id = license_document_file_id
    if national_id_document_file_id is not None:
        profile.national_id_document_file_id = national_id_document_file_id
    if selfie_document_file_id is not None:
        profile.selfie_document_file_id = selfie_document_file_id
    if license_document_url is not None:
        profile.license_document_url = _blank_to_none(license_document_url)
    if national_id_document_url is not None:
        profile.national_id_document_url = _blank_to_none(national_id_document_url)
    if selfie_document_url is not None:
        profile.selfie_document_url = _blank_to_none(selfie_document_url)


def _vehicle_payload(vehicle: Vehicle) -> dict:
    return {
        "id": str(vehicle.id),
        "plate_number": vehicle.plate_number,
        "make": vehicle.make,
        "model": vehicle.model,
        "color": vehicle.color,
        "category": vehicle.category.value,
        "comfort_level": vehicle.comfort_level.value,
        "registration_document_file_id": str(vehicle.registration_document_file_id)
        if vehicle.registration_document_file_id
        else None,
        "active": vehicle.active,
    }


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _review_note(notes: str | None, reviewed_by_user_id: UUID) -> str:
    cleaned = _blank_to_none(notes)
    suffix = f"reviewed_by={reviewed_by_user_id}"
    return f"{cleaned} ({suffix})" if cleaned else suffix
