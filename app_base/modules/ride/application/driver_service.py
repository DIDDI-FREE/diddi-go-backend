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
from app_base.core.observability import log_event
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    DriverProfile,
    DriverStatus,
    Vehicle,
    VehicleCategory,
    VehicleVerificationStatus,
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
        license_back_document_file_id: UUID | None = None,
        national_id_document_file_id: UUID | None = None,
        national_id_back_document_file_id: UUID | None = None,
        selfie_document_file_id: UUID | None = None,
        license_document_url: str | None = None,
        license_back_document_url: str | None = None,
        national_id_document_url: str | None = None,
        national_id_back_document_url: str | None = None,
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
            license_back_document_file_id=license_back_document_file_id,
            national_id_document_file_id=national_id_document_file_id,
            national_id_back_document_file_id=national_id_back_document_file_id,
            selfie_document_file_id=selfie_document_file_id,
            license_document_url=_blank_to_none(license_document_url),
            license_back_document_url=_blank_to_none(license_back_document_url),
            national_id_document_url=_blank_to_none(national_id_document_url),
            national_id_back_document_url=_blank_to_none(national_id_back_document_url),
            selfie_document_url=_blank_to_none(selfie_document_url),
            kyc_submitted_at=now,
            created_at=now,
            updated_at=now,
        )
        await self.driver_repo.save(profile)
        log_event("driver.kyc.submitted", driver_id=profile.id, user_id=user_id, status=profile.status.value)
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
        license_back_document_file_id: UUID | None = None,
        national_id_document_file_id: UUID | None = None,
        national_id_back_document_file_id: UUID | None = None,
        selfie_document_file_id: UUID | None = None,
        license_document_url: str | None = None,
        license_back_document_url: str | None = None,
        national_id_document_url: str | None = None,
        national_id_back_document_url: str | None = None,
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
            license_back_document_file_id=license_back_document_file_id,
            national_id_document_file_id=national_id_document_file_id,
            national_id_back_document_file_id=national_id_back_document_file_id,
            selfie_document_file_id=selfie_document_file_id,
            license_document_url=license_document_url,
            license_back_document_url=license_back_document_url,
            national_id_document_url=national_id_document_url,
            national_id_back_document_url=national_id_back_document_url,
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
        log_event("driver.kyc.resubmitted", driver_id=profile.id, user_id=user_id, status=profile.status.value)
        return _profile_payload(profile)

    async def approve_kyc(self, driver_id: UUID, *, reviewed_by_user_id: UUID, notes: str | None = None) -> dict:
        profile = await self.driver_repo.find_by_id(driver_id)
        if profile is None:
            raise ApiError(404, "DRIVER_PROFILE_NOT_FOUND", "Aucun profil chauffeur pour cet identifiant.")
        _ensure_kyc_documents_complete(profile)
        now = datetime.now(UTC)
        profile.status = DriverStatus.ACTIVE
        profile.license_verified_at = now
        profile.kyc_reviewed_at = now
        profile.kyc_review_notes = _review_note(notes, reviewed_by_user_id)
        profile.updated_at = now
        await self.driver_repo.save(profile)
        log_event(
            "driver.kyc.approved",
            driver_id=profile.id,
            user_id=profile.user_id,
            reviewed_by_user_id=reviewed_by_user_id,
        )
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
        log_event(
            "driver.kyc.rejected",
            level="warning",
            driver_id=profile.id,
            user_id=profile.user_id,
            reviewed_by_user_id=reviewed_by_user_id,
        )
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
        insurance_document_file_id: UUID | None = None,
        technical_inspection_document_file_id: UUID | None = None,
        transport_authorization_document_file_id: UUID | None = None,
        vehicle_photo_file_id: UUID | None = None,
        vehicle_front_photo_file_id: UUID | None = None,
        vehicle_back_photo_file_id: UUID | None = None,
        vehicle_left_photo_file_id: UUID | None = None,
        vehicle_right_photo_file_id: UUID | None = None,
        vehicle_interior_photo_file_id: UUID | None = None,
        registration_document_url: str | None = None,
        insurance_document_url: str | None = None,
        technical_inspection_document_url: str | None = None,
        transport_authorization_document_url: str | None = None,
        vehicle_photo_url: str | None = None,
        vehicle_front_photo_url: str | None = None,
        vehicle_back_photo_url: str | None = None,
        vehicle_left_photo_url: str | None = None,
        vehicle_right_photo_url: str | None = None,
        vehicle_interior_photo_url: str | None = None,
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
            insurance_document_file_id=insurance_document_file_id,
            technical_inspection_document_file_id=technical_inspection_document_file_id,
            transport_authorization_document_file_id=transport_authorization_document_file_id,
            vehicle_photo_file_id=vehicle_photo_file_id,
            vehicle_front_photo_file_id=vehicle_front_photo_file_id,
            vehicle_back_photo_file_id=vehicle_back_photo_file_id,
            vehicle_left_photo_file_id=vehicle_left_photo_file_id,
            vehicle_right_photo_file_id=vehicle_right_photo_file_id,
            vehicle_interior_photo_file_id=vehicle_interior_photo_file_id,
            registration_document_url=_blank_to_none(registration_document_url),
            insurance_document_url=_blank_to_none(insurance_document_url),
            technical_inspection_document_url=_blank_to_none(technical_inspection_document_url),
            transport_authorization_document_url=_blank_to_none(transport_authorization_document_url),
            vehicle_photo_url=_blank_to_none(vehicle_photo_url),
            vehicle_front_photo_url=_blank_to_none(vehicle_front_photo_url),
            vehicle_back_photo_url=_blank_to_none(vehicle_back_photo_url),
            vehicle_left_photo_url=_blank_to_none(vehicle_left_photo_url),
            vehicle_right_photo_url=_blank_to_none(vehicle_right_photo_url),
            vehicle_interior_photo_url=_blank_to_none(vehicle_interior_photo_url),
            verification_status=VehicleVerificationStatus.PENDING_VERIFICATION,
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
        log_event(
            "driver.vehicle.registered",
            driver_id=profile.id,
            user_id=user_id,
            vehicle_id=vehicle.id,
            category=vehicle.category.value,
            comfort_level=vehicle.comfort_level.value,
            verification_status=vehicle.verification_status.value,
        )
        return _vehicle_payload(vehicle)

    async def resubmit_vehicle_kyv(
        self,
        vehicle_id: UUID,
        *,
        user_id: UUID,
        registration_document_file_id: UUID | None = None,
        insurance_document_file_id: UUID | None = None,
        technical_inspection_document_file_id: UUID | None = None,
        transport_authorization_document_file_id: UUID | None = None,
        vehicle_photo_file_id: UUID | None = None,
        vehicle_front_photo_file_id: UUID | None = None,
        vehicle_back_photo_file_id: UUID | None = None,
        vehicle_left_photo_file_id: UUID | None = None,
        vehicle_right_photo_file_id: UUID | None = None,
        vehicle_interior_photo_file_id: UUID | None = None,
        registration_document_url: str | None = None,
        insurance_document_url: str | None = None,
        technical_inspection_document_url: str | None = None,
        transport_authorization_document_url: str | None = None,
        vehicle_photo_url: str | None = None,
        vehicle_front_photo_url: str | None = None,
        vehicle_back_photo_url: str | None = None,
        vehicle_left_photo_url: str | None = None,
        vehicle_right_photo_url: str | None = None,
        vehicle_interior_photo_url: str | None = None,
    ) -> dict:
        profile = await self._require_profile(user_id)
        vehicle = await self._require_vehicle(vehicle_id)
        if vehicle.driver_id != profile.id:
            raise ApiError(403, ErrorCode.RIDE_NOT_OWNED_BY_USER, "Ce vehicule n'appartient pas a ce chauffeur.")
        _update_vehicle_kyv_fields(
            vehicle,
            registration_document_file_id=registration_document_file_id,
            insurance_document_file_id=insurance_document_file_id,
            technical_inspection_document_file_id=technical_inspection_document_file_id,
            transport_authorization_document_file_id=transport_authorization_document_file_id,
            vehicle_photo_file_id=vehicle_photo_file_id,
            vehicle_front_photo_file_id=vehicle_front_photo_file_id,
            vehicle_back_photo_file_id=vehicle_back_photo_file_id,
            vehicle_left_photo_file_id=vehicle_left_photo_file_id,
            vehicle_right_photo_file_id=vehicle_right_photo_file_id,
            vehicle_interior_photo_file_id=vehicle_interior_photo_file_id,
            registration_document_url=registration_document_url,
            insurance_document_url=insurance_document_url,
            technical_inspection_document_url=technical_inspection_document_url,
            transport_authorization_document_url=transport_authorization_document_url,
            vehicle_photo_url=vehicle_photo_url,
            vehicle_front_photo_url=vehicle_front_photo_url,
            vehicle_back_photo_url=vehicle_back_photo_url,
            vehicle_left_photo_url=vehicle_left_photo_url,
            vehicle_right_photo_url=vehicle_right_photo_url,
            vehicle_interior_photo_url=vehicle_interior_photo_url,
        )
        vehicle.verification_status = VehicleVerificationStatus.PENDING_VERIFICATION
        vehicle.verified_at = None
        vehicle.reviewed_at = None
        vehicle.review_notes = None
        await self.vehicle_repo.save(vehicle)
        log_event("driver.vehicle.kyv.resubmitted", driver_id=profile.id, user_id=user_id, vehicle_id=vehicle.id)
        return _vehicle_payload(vehicle)

    async def approve_vehicle_kyv(
        self,
        vehicle_id: UUID,
        *,
        reviewed_by_user_id: UUID,
        notes: str | None = None,
    ) -> dict:
        vehicle = await self._require_vehicle(vehicle_id)
        _ensure_vehicle_kyv_documents_complete(vehicle)
        now = datetime.now(UTC)
        vehicle.verification_status = VehicleVerificationStatus.ACTIVE
        vehicle.verified_at = now
        vehicle.reviewed_at = now
        vehicle.review_notes = _review_note(notes, reviewed_by_user_id)
        vehicle.active = True
        await self.vehicle_repo.save(vehicle)
        log_event("driver.vehicle.kyv.approved", vehicle_id=vehicle.id, driver_id=vehicle.driver_id)
        return _vehicle_payload(vehicle)

    async def reject_vehicle_kyv(
        self,
        vehicle_id: UUID,
        *,
        reviewed_by_user_id: UUID,
        notes: str | None = None,
    ) -> dict:
        vehicle = await self._require_vehicle(vehicle_id)
        vehicle.verification_status = VehicleVerificationStatus.REJECTED
        vehicle.verified_at = None
        vehicle.reviewed_at = datetime.now(UTC)
        vehicle.review_notes = _review_note(notes, reviewed_by_user_id)
        vehicle.active = False
        await self.vehicle_repo.save(vehicle)
        log_event("driver.vehicle.kyv.rejected", level="warning", vehicle_id=vehicle.id, driver_id=vehicle.driver_id)
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

    async def list_vehicle_kyv_queue(
        self,
        *,
        status: str = "pending_verification",
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        if status == "all":
            statuses = [
                VehicleVerificationStatus.PENDING_VERIFICATION,
                VehicleVerificationStatus.ACTIVE,
                VehicleVerificationStatus.SUSPENDED,
                VehicleVerificationStatus.REJECTED,
            ]
        else:
            try:
                statuses = [VehicleVerificationStatus(status)]
            except ValueError as exc:
                raise ApiError(
                    422,
                    ErrorCode.INVALID_VEHICLE_STATUS,
                    "Statut KYV vehicule invalide.",
                    {
                        "field": "status",
                        "allowed": ["pending_verification", "active", "suspended", "rejected", "all"],
                    },
                ) from exc
        vehicles, total = await self.vehicle_repo.list_by_verification_status(
            [item.value for item in statuses],
            page=page,
            page_size=page_size,
        )
        return {
            "data": [_vehicle_payload(vehicle) for vehicle in vehicles],
            "pagination": {"page": page, "page_size": page_size, "total": total},
        }

    async def resolve_driver(self, user_id: UUID) -> tuple[DriverProfile, Vehicle]:
        """Profile + active vehicle for a driver about to go online or take a
        ride. Raises if either is missing — matching must never hand a ride to
        a driver with no vehicle on file."""
        profile = await self._require_profile(user_id)
        if profile.status != DriverStatus.ACTIVE:
            log_event(
                "driver.online.blocked",
                level="warning",
                driver_id=profile.id,
                user_id=user_id,
                reason="driver_not_verified",
                status=profile.status.value,
            )
            raise ApiError(
                403,
                "DRIVER_NOT_VERIFIED",
                "Votre profil chauffeur n'est pas encore validé.",
                {"status": profile.status.value},
            )
        vehicle = await self.vehicle_repo.find_active_for_driver(profile.id)
        if vehicle is None:
            log_event(
                "driver.online.blocked",
                level="warning",
                driver_id=profile.id,
                user_id=user_id,
                reason="no_active_vehicle",
            )
            raise ApiError(
                409, "NO_ACTIVE_VEHICLE", "Aucun véhicule actif n'est associé à ce chauffeur.",
            )
        if vehicle.verification_status != VehicleVerificationStatus.ACTIVE:
            log_event(
                "driver.online.blocked",
                level="warning",
                driver_id=profile.id,
                user_id=user_id,
                reason="vehicle_not_verified",
                vehicle_id=vehicle.id,
                vehicle_status=vehicle.verification_status.value,
            )
            raise ApiError(
                403,
                ErrorCode.VEHICLE_NOT_VERIFIED,
                "Votre vehicule n'est pas encore valide.",
                {"vehicle_id": str(vehicle.id), "status": vehicle.verification_status.value},
            )
        return profile, vehicle

    async def _require_profile(self, user_id: UUID) -> DriverProfile:
        profile = await self.driver_repo.find_by_user_id(user_id)
        if profile is None:
            raise ApiError(
                404, "DRIVER_PROFILE_NOT_FOUND", "Aucun profil chauffeur pour ce compte.",
            )
        return profile

    async def _require_vehicle(self, vehicle_id: UUID) -> Vehicle:
        vehicle = await self.vehicle_repo.find_by_id(vehicle_id)
        if vehicle is None:
            raise ApiError(404, ErrorCode.VEHICLE_NOT_FOUND, "Vehicule introuvable.")
        return vehicle


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
            "license_back_document_file_id": str(profile.license_back_document_file_id)
            if profile.license_back_document_file_id
            else None,
            "national_id_document_file_id": str(profile.national_id_document_file_id)
            if profile.national_id_document_file_id
            else None,
            "national_id_back_document_file_id": str(profile.national_id_back_document_file_id)
            if profile.national_id_back_document_file_id
            else None,
            "selfie_document_file_id": str(profile.selfie_document_file_id)
            if profile.selfie_document_file_id
            else None,
            "license_document_url": profile.license_document_url,
            "license_back_document_url": profile.license_back_document_url,
            "national_id_document_url": profile.national_id_document_url,
            "national_id_back_document_url": profile.national_id_back_document_url,
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
    license_back_document_file_id: UUID | None,
    national_id_document_file_id: UUID | None,
    national_id_back_document_file_id: UUID | None,
    selfie_document_file_id: UUID | None,
    license_document_url: str | None,
    license_back_document_url: str | None,
    national_id_document_url: str | None,
    national_id_back_document_url: str | None,
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
    if license_back_document_file_id is not None:
        profile.license_back_document_file_id = license_back_document_file_id
    if national_id_document_file_id is not None:
        profile.national_id_document_file_id = national_id_document_file_id
    if national_id_back_document_file_id is not None:
        profile.national_id_back_document_file_id = national_id_back_document_file_id
    if selfie_document_file_id is not None:
        profile.selfie_document_file_id = selfie_document_file_id
    if license_document_url is not None:
        profile.license_document_url = _blank_to_none(license_document_url)
    if license_back_document_url is not None:
        profile.license_back_document_url = _blank_to_none(license_back_document_url)
    if national_id_document_url is not None:
        profile.national_id_document_url = _blank_to_none(national_id_document_url)
    if national_id_back_document_url is not None:
        profile.national_id_back_document_url = _blank_to_none(national_id_back_document_url)
    if selfie_document_url is not None:
        profile.selfie_document_url = _blank_to_none(selfie_document_url)


def _ensure_kyc_documents_complete(profile: DriverProfile) -> None:
    missing = [
        key
        for key, present in {
            "license_document": bool(profile.license_document_file_id or profile.license_document_url),
            "license_back_document": bool(profile.license_back_document_file_id or profile.license_back_document_url),
            "national_id_document": bool(profile.national_id_document_file_id or profile.national_id_document_url),
            "national_id_back_document": bool(
                profile.national_id_back_document_file_id or profile.national_id_back_document_url
            ),
            "selfie_document": bool(profile.selfie_document_file_id or profile.selfie_document_url),
        }.items()
        if not present
    ]
    if missing:
        raise ApiError(
            422,
            ErrorCode.INVALID_KYC_DOCUMENTS,
            "Le dossier KYC chauffeur est incomplet.",
            {"missing_documents": missing},
        )


def _vehicle_payload(vehicle: Vehicle) -> dict:
    return {
        "id": str(vehicle.id),
        "driver_id": str(vehicle.driver_id),
        "plate_number": vehicle.plate_number,
        "make": vehicle.make,
        "model": vehicle.model,
        "color": vehicle.color,
        "category": vehicle.category.value,
        "comfort_level": vehicle.comfort_level.value,
        "registration_document_file_id": str(vehicle.registration_document_file_id)
        if vehicle.registration_document_file_id
        else None,
        "insurance_document_file_id": str(vehicle.insurance_document_file_id)
        if vehicle.insurance_document_file_id
        else None,
        "technical_inspection_document_file_id": str(vehicle.technical_inspection_document_file_id)
        if vehicle.technical_inspection_document_file_id
        else None,
        "transport_authorization_document_file_id": str(vehicle.transport_authorization_document_file_id)
        if vehicle.transport_authorization_document_file_id
        else None,
        "vehicle_photo_file_id": str(vehicle.vehicle_photo_file_id) if vehicle.vehicle_photo_file_id else None,
        "vehicle_front_photo_file_id": str(vehicle.vehicle_front_photo_file_id)
        if vehicle.vehicle_front_photo_file_id
        else None,
        "vehicle_back_photo_file_id": str(vehicle.vehicle_back_photo_file_id)
        if vehicle.vehicle_back_photo_file_id
        else None,
        "vehicle_left_photo_file_id": str(vehicle.vehicle_left_photo_file_id)
        if vehicle.vehicle_left_photo_file_id
        else None,
        "vehicle_right_photo_file_id": str(vehicle.vehicle_right_photo_file_id)
        if vehicle.vehicle_right_photo_file_id
        else None,
        "vehicle_interior_photo_file_id": str(vehicle.vehicle_interior_photo_file_id)
        if vehicle.vehicle_interior_photo_file_id
        else None,
        "registration_document_url": vehicle.registration_document_url,
        "insurance_document_url": vehicle.insurance_document_url,
        "technical_inspection_document_url": vehicle.technical_inspection_document_url,
        "transport_authorization_document_url": vehicle.transport_authorization_document_url,
        "vehicle_photo_url": vehicle.vehicle_photo_url,
        "vehicle_front_photo_url": vehicle.vehicle_front_photo_url,
        "vehicle_back_photo_url": vehicle.vehicle_back_photo_url,
        "vehicle_left_photo_url": vehicle.vehicle_left_photo_url,
        "vehicle_right_photo_url": vehicle.vehicle_right_photo_url,
        "vehicle_interior_photo_url": vehicle.vehicle_interior_photo_url,
        "verification_status": vehicle.verification_status.value,
        "verified_at": vehicle.verified_at.isoformat() if vehicle.verified_at else None,
        "reviewed_at": vehicle.reviewed_at.isoformat() if vehicle.reviewed_at else None,
        "review_notes": vehicle.review_notes,
        "owner_type": vehicle.owner_type,
        "partner_id": str(vehicle.partner_id) if vehicle.partner_id else None,
        "active": vehicle.active,
    }


def _update_vehicle_kyv_fields(
    vehicle: Vehicle,
    *,
    registration_document_file_id: UUID | None,
    insurance_document_file_id: UUID | None,
    technical_inspection_document_file_id: UUID | None,
    transport_authorization_document_file_id: UUID | None,
    vehicle_photo_file_id: UUID | None,
    vehicle_front_photo_file_id: UUID | None,
    vehicle_back_photo_file_id: UUID | None,
    vehicle_left_photo_file_id: UUID | None,
    vehicle_right_photo_file_id: UUID | None,
    vehicle_interior_photo_file_id: UUID | None,
    registration_document_url: str | None,
    insurance_document_url: str | None,
    technical_inspection_document_url: str | None,
    transport_authorization_document_url: str | None,
    vehicle_photo_url: str | None,
    vehicle_front_photo_url: str | None,
    vehicle_back_photo_url: str | None,
    vehicle_left_photo_url: str | None,
    vehicle_right_photo_url: str | None,
    vehicle_interior_photo_url: str | None,
) -> None:
    if registration_document_file_id is not None:
        vehicle.registration_document_file_id = registration_document_file_id
    if insurance_document_file_id is not None:
        vehicle.insurance_document_file_id = insurance_document_file_id
    if technical_inspection_document_file_id is not None:
        vehicle.technical_inspection_document_file_id = technical_inspection_document_file_id
    if transport_authorization_document_file_id is not None:
        vehicle.transport_authorization_document_file_id = transport_authorization_document_file_id
    if vehicle_photo_file_id is not None:
        vehicle.vehicle_photo_file_id = vehicle_photo_file_id
    if vehicle_front_photo_file_id is not None:
        vehicle.vehicle_front_photo_file_id = vehicle_front_photo_file_id
    if vehicle_back_photo_file_id is not None:
        vehicle.vehicle_back_photo_file_id = vehicle_back_photo_file_id
    if vehicle_left_photo_file_id is not None:
        vehicle.vehicle_left_photo_file_id = vehicle_left_photo_file_id
    if vehicle_right_photo_file_id is not None:
        vehicle.vehicle_right_photo_file_id = vehicle_right_photo_file_id
    if vehicle_interior_photo_file_id is not None:
        vehicle.vehicle_interior_photo_file_id = vehicle_interior_photo_file_id
    if registration_document_url is not None:
        vehicle.registration_document_url = _blank_to_none(registration_document_url)
    if insurance_document_url is not None:
        vehicle.insurance_document_url = _blank_to_none(insurance_document_url)
    if technical_inspection_document_url is not None:
        vehicle.technical_inspection_document_url = _blank_to_none(technical_inspection_document_url)
    if transport_authorization_document_url is not None:
        vehicle.transport_authorization_document_url = _blank_to_none(transport_authorization_document_url)
    if vehicle_photo_url is not None:
        vehicle.vehicle_photo_url = _blank_to_none(vehicle_photo_url)
    if vehicle_front_photo_url is not None:
        vehicle.vehicle_front_photo_url = _blank_to_none(vehicle_front_photo_url)
    if vehicle_back_photo_url is not None:
        vehicle.vehicle_back_photo_url = _blank_to_none(vehicle_back_photo_url)
    if vehicle_left_photo_url is not None:
        vehicle.vehicle_left_photo_url = _blank_to_none(vehicle_left_photo_url)
    if vehicle_right_photo_url is not None:
        vehicle.vehicle_right_photo_url = _blank_to_none(vehicle_right_photo_url)
    if vehicle_interior_photo_url is not None:
        vehicle.vehicle_interior_photo_url = _blank_to_none(vehicle_interior_photo_url)


def _ensure_vehicle_kyv_documents_complete(vehicle: Vehicle) -> None:
    missing = [
        key
        for key, present in {
            "registration_document": bool(vehicle.registration_document_file_id or vehicle.registration_document_url),
            "insurance_document": bool(vehicle.insurance_document_file_id or vehicle.insurance_document_url),
            "technical_inspection_document": bool(
                vehicle.technical_inspection_document_file_id or vehicle.technical_inspection_document_url
            ),
            "vehicle_front_photo": bool(vehicle.vehicle_front_photo_file_id or vehicle.vehicle_front_photo_url),
            "vehicle_back_photo": bool(vehicle.vehicle_back_photo_file_id or vehicle.vehicle_back_photo_url),
            "vehicle_left_photo": bool(vehicle.vehicle_left_photo_file_id or vehicle.vehicle_left_photo_url),
            "vehicle_right_photo": bool(vehicle.vehicle_right_photo_file_id or vehicle.vehicle_right_photo_url),
            "vehicle_interior_photo": bool(
                vehicle.vehicle_interior_photo_file_id or vehicle.vehicle_interior_photo_url
            ),
        }.items()
        if not present
    ]
    if missing:
        raise ApiError(
            422,
            ErrorCode.INVALID_VEHICLE_KYV_DOCUMENTS,
            "Le dossier KYV vehicule est incomplet.",
            {"missing_documents": missing},
        )


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _review_note(notes: str | None, reviewed_by_user_id: UUID) -> str:
    cleaned = _blank_to_none(notes)
    suffix = f"reviewed_by={reviewed_by_user_id}"
    return f"{cleaned} ({suffix})" if cleaned else suffix
