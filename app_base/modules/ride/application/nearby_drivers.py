"""Anonymous, bounded availability preview before a passenger requests a ride."""

from dataclasses import dataclass

from app_base.modules.ride.application.driver_online_eligibility import DriverOnlineEligibilityService
from app_base.modules.ride.application.matching_service import _comfort_can_serve
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    DriverStatus,
    VehicleCategory,
    VehicleVerificationStatus,
)
from app_base.modules.ride.domain.interfaces import (
    DriverLocationService,
    DriverProfileRepository,
    RideRepository,
    VehicleRepository,
)
from app_base.shared_kernel.types import GeoPoint

MAX_PREVIEW_CANDIDATES = 100


@dataclass
class NearbyDriversService:
    drivers: DriverProfileRepository
    vehicles: VehicleRepository
    rides: RideRepository
    locations: DriverLocationService
    eligibility: DriverOnlineEligibilityService

    async def search(
        self,
        *,
        origin: GeoPoint,
        radius_km: float,
        limit: int,
        vehicle_category: VehicleCategory,
        comfort_level: ComfortLevel,
        is_review_account: bool,
    ) -> dict:
        candidates = await self.locations.find_available_nearby(
            origin, radius_km=radius_km, limit=MAX_PREVIEW_CANDIDATES,
        )
        positions = await self.locations.coordinates_for(candidates)
        markers = []
        for user_id in candidates:
            position = positions.get(user_id)
            if position is None:
                continue
            profile = await self.drivers.find_by_user_id(user_id)
            if (
                profile is None
                or profile.status != DriverStatus.ACTIVE
                or profile.is_review_account != is_review_account
            ):
                continue
            vehicle = await self.vehicles.find_active_for_driver(profile.id)
            if (
                vehicle is None
                or vehicle.verification_status != VehicleVerificationStatus.ACTIVE
                or vehicle.category != vehicle_category
                or not _comfort_can_serve(vehicle.comfort_level, comfort_level)
            ):
                continue
            # A stale availability marker must never expose a driver mid-ride.
            if await self.rides.find_active_by_driver_user_id(user_id) is not None:
                continue
            if not (await self.eligibility.evaluate(profile.id))["eligible"]:
                continue
            markers.append({
                "position": {"lat": round(position.lat, 3), "lng": round(position.lng, 3)},
                "vehicle_category": vehicle.category.value,
                "comfort_level": vehicle.comfort_level.value,
            })
            if len(markers) >= limit:
                break
        return {"drivers": markers, "radius_km": radius_km, "approximate": True}
