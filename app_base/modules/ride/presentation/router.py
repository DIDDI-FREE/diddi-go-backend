"""Ride router — `/v1/rides/*` endpoints per API contract §2.

All handlers are async (DB/Redis backed) and receive their service deps via
FastAPI `Depends`. Protected endpoints require `get_current_user`; driver-
only routes additionally gate on `current_user.role == "driver"`.

The matching engine is deferred (architecture doc §7 step 3), so today a
ride is driven forward explicitly rather than by automatic assignment:

  POST /rides                                     → status=requested
  PATCH /rides/{id}/status {"status": "matched"}  → driver-driven
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app_base.core.auth_deps import get_current_user, require_business_driver
from app_base.core.deps import get_diddimap, matching_service, ride_service
from app_base.core.errors import ApiError
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.ride.application.matching_service import MatchingService
from app_base.modules.ride.application.services import RideService, iso_utc, ride_creation_payload
from app_base.modules.ride.domain.entities import DriverProfile, RideStatus
from app_base.modules.ride.infra.offer_store import OFFER_TTL_SECONDS
from app_base.modules.ride.infra.routing_client import DiddiMapRoutingClient
from app_base.modules.ride.presentation.schemas import (
    PlaceSearchResponseItem,
    PricingEstimateRequest,
    RideCancelRequest,
    RideCreateRequest,
    RideRatingRequest,
    RideStatusUpdateRequest,
)
from app_base.modules.ride.presentation.websocket import manager
from app_base.shared_kernel.types import GeoPoint

router = APIRouter(prefix="/rides", tags=["ride"])
places_router = APIRouter(prefix="/places", tags=["places"])


@places_router.get("/search", response_model=list[PlaceSearchResponseItem])
async def search_places(
    q: str = Query(..., min_length=2, max_length=120),
    bias_lat: float | None = Query(default=None, ge=-90, le=90),
    bias_lng: float | None = Query(default=None, ge=-180, le=180),
    limit: int = Query(default=10, ge=1, le=20),
    diddimap: DiddiMapRoutingClient = Depends(get_diddimap),
) -> list[PlaceSearchResponseItem]:
    """Search pickup/dropoff places through DiddiMap/AbidjanMaps.

    `bias_lat` + `bias_lng` are optional and help rank results around the
    user's current position. If only one is sent, the bias is ignored.
    """
    bias = GeoPoint(lat=bias_lat, lng=bias_lng) if bias_lat is not None and bias_lng is not None else None
    results = await diddimap.geocode(q, bias=bias)
    return [
        PlaceSearchResponseItem(label=item.label, lat=item.point.lat, lng=item.point.lng)
        for item in results[:limit]
    ]


@router.post("/pricing/estimate")
async def estimate_pricing(
    payload: PricingEstimateRequest,
    service: RideService = Depends(ride_service),
) -> dict:
    pickup = GeoPoint(lat=payload.pickup.lat, lng=payload.pickup.lng)
    dropoff = GeoPoint(lat=payload.dropoff.lat, lng=payload.dropoff.lng)
    return await service.estimate_pricing(pickup, dropoff, payload.vehicle_category)


@router.post("", status_code=201)
async def create_ride(
    payload: RideCreateRequest,
    service: RideService = Depends(ride_service),
    matching: MatchingService = Depends(matching_service),
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    """Create a ride and immediately offer it to the nearest driver.

    The response always reports `status: "requested"` as the API contract
    §2 specifies — matching runs inline, but no driver has answered yet, so
    the passenger learns the outcome over the WebSocket rather than here.
    That holds even when no driver could be offered: the ride is already
    `no_driver_found` in the database and the `ride.no_driver_found` event is
    on its way, but the creation response keeps its contractual shape.
    """
    pickup = GeoPoint(lat=payload.pickup.lat, lng=payload.pickup.lng)
    dropoff = GeoPoint(lat=payload.dropoff.lat, lng=payload.dropoff.lng)
    ride = await service.request_ride(
        passenger_user_id=current_user.id,
        pickup=pickup,
        pickup_address=payload.pickup.address,
        dropoff=dropoff,
        dropoff_address=payload.dropoff.address,
        vehicle_category=payload.vehicle_category,
        scheduled_at=payload.scheduled_at,
    )
    response = ride_creation_payload(ride)

    offered_to = await matching.try_match(ride)
    if offered_to is not None:
        await manager.send_new_request(
            offered_to,
            {
                "ride_id": str(ride.id),
                "pickup": {
                    "lat": pickup.lat,
                    "lng": pickup.lng,
                    "address": payload.pickup.address,
                },
                "dropoff_address": payload.dropoff.address,
                "estimated_fare": int(ride.estimated_fare) if ride.estimated_fare else None,
                "expires_in_seconds": OFFER_TTL_SECONDS,
            },
        )
    elif ride.status is RideStatus.NO_DRIVER_FOUND:
        await manager.broadcast_no_driver_found(ride.id)

    return response


@router.post("/{ride_id}/accept")
async def accept_ride(
    ride_id: UUID,
    matching: MatchingService = Depends(matching_service),
    current_user: UserModel = Depends(get_current_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    """Driver accepts the ride they were offered (API contract §4).

    Only the driver currently holding the offer may accept, and only one
    accept can win — a second arrival gets `409 RIDE_ALREADY_MATCHED`.
    """
    ride = await matching.accept(ride_id, current_user.id)
    await manager.broadcast_status_changed(ride.id, ride.status.value)
    return {
        "ride_id": str(ride.id),
        "status": ride.status.value,
        "driver_id": str(ride.driver_id) if ride.driver_id else None,
        "vehicle_id": str(ride.vehicle_id) if ride.vehicle_id else None,
        "matched_at": iso_utc(ride.matched_at),
    }


@router.post("/{ride_id}/decline")
async def decline_ride(
    ride_id: UUID,
    matching: MatchingService = Depends(matching_service),
    service: RideService = Depends(ride_service),
    current_user: UserModel = Depends(get_current_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    """Driver declines; the offer moves to the next-nearest candidate."""
    next_driver = await matching.decline(ride_id, current_user.id)
    if next_driver is not None:
        ride = await service.load_ride(ride_id)
        await manager.send_new_request(
            next_driver,
            {
                "ride_id": str(ride_id),
                "pickup": {
                    "lat": ride.pickup_location.lat if ride.pickup_location else None,
                    "lng": ride.pickup_location.lng if ride.pickup_location else None,
                    "address": ride.pickup_address,
                },
                "dropoff_address": ride.dropoff_address,
                "estimated_fare": int(ride.estimated_fare) if ride.estimated_fare else None,
                "expires_in_seconds": OFFER_TTL_SECONDS,
            },
        )
    else:
        await manager.broadcast_no_driver_found(ride_id)
    return {"ride_id": str(ride_id), "reoffered": next_driver is not None}


@router.get("/{ride_id}")
async def get_ride(
    ride_id: UUID,
    service: RideService = Depends(ride_service),
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    return await service.get_ride(ride_id, actor_user_id=current_user.id, actor_role=current_user.role)


@router.get("")
async def list_rides(
    service: RideService = Depends(ride_service),
    current_user: UserModel = Depends(get_current_user),
    role: str | None = None,
    status: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    active_role = role or current_user.role
    status_enum = RideStatus(status) if status else None
    return await service.list_rides(
        actor_user_id=current_user.id,
        actor_role=active_role,
        passenger_user_id=None,  # admin-only scope expansion not implemented
        driver_id=None,
        status=status_enum,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )


@router.patch("/{ride_id}/status")
async def update_status(
    ride_id: UUID,
    payload: RideStatusUpdateRequest,
    service: RideService = Depends(ride_service),
    matching: MatchingService = Depends(matching_service),
    current_user: UserModel = Depends(get_current_user),
    _driver_profile: DriverProfile | None = Depends(require_business_driver),
) -> dict:
    if current_user.role != "admin" and _driver_profile is None:
        raise ApiError(403, "FORBIDDEN_ROLE", "Seul le chauffeur peut mettre à jour l'état.")
    try:
        new_status = RideStatus(payload.status)
    except ValueError as exc:
        raise ApiError(422, "INVALID_STATUS", f"Statut inconnu: {payload.status}") from exc
    result = await service.update_status(
        ride_id,
        new_status,
        actor_user_id=current_user.id,
    )
    if new_status is RideStatus.COMPLETED:
        # Ride is over: the driver returns to the matching pool.
        await matching.release_driver(await service.load_ride(ride_id))
    await manager.broadcast_status_changed(ride_id, new_status.value)
    return result


@router.post("/{ride_id}/cancel")
async def cancel_ride(
    ride_id: UUID,
    payload: RideCancelRequest,
    service: RideService = Depends(ride_service),
    matching: MatchingService = Depends(matching_service),
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    result = await service.cancel(
        ride_id,
        payload.reason,
        actor_role=current_user.role,
    )
    # Frees an assigned driver and drops any outstanding offer, so a cancelled
    # ride never leaves a driver pinned or an offer dangling.
    await matching.release_driver(await service.load_ride(ride_id))
    await manager.broadcast_status_changed(ride_id, result["status"])
    return result


@router.post("/{ride_id}/rating", status_code=201)
async def rate_ride(
    ride_id: UUID,
    payload: RideRatingRequest,
    service: RideService = Depends(ride_service),
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    return await service.rate(
        ride_id,
        payload.rating,
        payload.comment,
        actor_role=current_user.role,
    )
