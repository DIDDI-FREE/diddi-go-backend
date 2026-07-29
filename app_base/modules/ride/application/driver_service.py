"""Driver onboarding use cases.

A `driver` user in `auth.users` is not yet a driver who can take rides: they
need a `ride.driver_profiles` row (licence, KYC status) and at least one
active `ride.vehicles` row. This service owns that onboarding path.

KYC note: `license_verified_at` is left NULL and `status` starts at
`pending_verification`. An admin endpoint to approve drivers is still
outstanding, so `APPROVE_DRIVERS_ON_CREATE` decides whether a freshly
registered driver may go online immediately. It defaults to True while
there is no back-office, and must be flipped off once one exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app_base.core.errors import ApiError
from app_base.modules.ride.domain.entities import (
    DriverProfile,
    DriverStatus,
    Vehicle,
    VehicleCategory,
)
from app_base.modules.ride.domain.interfaces import (
    DriverProfileRepository,
    VehicleRepository,
)

# Until a back-office exists, a driver who submits a licence is usable right
# away. Flip to False the moment an admin KYC endpoint ships, or unverified
# drivers will keep being matched to passengers.
APPROVE_DRIVERS_ON_CREATE = True


@dataclass
class DriverService:
    driver_repo: DriverProfileRepository
    vehicle_repo: VehicleRepository

    async def create_profile(
        self,
        *,
        user_id: UUID,
        license_number: str,
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
            status=DriverStatus.ACTIVE if APPROVE_DRIVERS_ON_CREATE else DriverStatus.PENDING_VERIFICATION,
            license_verified_at=now if APPROVE_DRIVERS_ON_CREATE else None,
            created_at=now,
            updated_at=now,
        )
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
    ) -> dict:
        if category not in {c.value for c in VehicleCategory}:
            raise ApiError(
                422, "INVALID_VEHICLE_CATEGORY", "Catégorie de véhicule invalide.",
                {"field": "category"},
            )
        profile = await self._require_profile(user_id)

        vehicle = Vehicle(
            id=Vehicle.new_id(),
            driver_id=profile.id,
            plate_number=plate_number.strip().upper(),
            make=make,
            model=model,
            color=color,
            category=VehicleCategory(category),
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
    }


def _vehicle_payload(vehicle: Vehicle) -> dict:
    return {
        "id": str(vehicle.id),
        "plate_number": vehicle.plate_number,
        "make": vehicle.make,
        "model": vehicle.model,
        "color": vehicle.color,
        "category": vehicle.category.value,
        "active": vehicle.active,
    }
