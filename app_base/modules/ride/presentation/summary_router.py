"""Internal, scoped service-to-service reporting endpoint."""

from fastapi import APIRouter, Depends, Query

from app_base.core.auth_deps import require_identity_service_token
from app_base.core.deps import ride_summary_service
from app_base.modules.ride.application.summary_service import RideSummaryService

router = APIRouter(prefix="/internal/v1", tags=["internal-ride-summary"])
require_pilotage = require_identity_service_token(
    audience="diddigo",
    required_scope="ride-summary:read",
    expected_subject="service:pilotage",
)


@router.get("/ride-summary")
async def get_ride_summary(
    day: str = Query(alias="date"),
    _claims: dict = Depends(require_pilotage),
    service: RideSummaryService = Depends(ride_summary_service),
) -> dict:
    return await service.daily_summary(day)
