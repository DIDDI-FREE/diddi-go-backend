"""Internal, scoped service-to-service reporting endpoint."""

from fastapi import APIRouter, Depends, Query

from app_base.core.auth_deps import require_identity_service_token
from app_base.core.deps import ride_summary_service
from app_base.core.service_scopes import DIDDIGO_AUDIENCE, RIDE_SUMMARY_READ
from app_base.modules.ride.application.summary_service import RideSummaryService

router = APIRouter(tags=["internal-ride-summary"])
require_pilotage = require_identity_service_token(
    audience=DIDDIGO_AUDIENCE,
    required_scope=RIDE_SUMMARY_READ,
    expected_subject="service:pilotage",
)


@router.get("/internal/v1/ride-summary")
async def get_ride_summary(
    day: str = Query(alias="date"),
    _claims: dict = Depends(require_pilotage),
    service: RideSummaryService = Depends(ride_summary_service),
) -> dict:
    return await service.daily_summary(day)


@router.get("/internal/pilotage/daily-summary")
async def get_pilotage_daily_summary(
    day: str = Query(alias="date"),
    _claims: dict = Depends(require_pilotage),
    service: RideSummaryService = Depends(ride_summary_service),
) -> dict:
    return await service.pilotage_daily_summary(day)
