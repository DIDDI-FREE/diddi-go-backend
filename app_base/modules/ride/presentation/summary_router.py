"""Internal, scoped service-to-service reporting endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request

from app_base.core.auth_deps import require_identity_service_token
from app_base.core.database import database_ready
from app_base.core.deps import ride_breakdown_service, ride_summary_service
from app_base.core.service_scopes import DIDDIGO_AUDIENCE, RIDE_SUMMARY_READ
from app_base.modules.ride.application.breakdown_service import RideBreakdownService
from app_base.modules.ride.application.summary_service import RideSummaryService
from app_base.modules.ride.presentation.summary_schemas import PilotageFinanceSummaryResponse

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


@router.get("/internal/pilotage/finance-summary", response_model=PilotageFinanceSummaryResponse)
async def get_pilotage_finance_summary(
    day: str = Query(alias="date"),
    _claims: dict = Depends(require_pilotage),
    service: RideSummaryService = Depends(ride_summary_service),
) -> PilotageFinanceSummaryResponse:
    return PilotageFinanceSummaryResponse.model_validate(await service.pilotage_finance_summary(day))


@router.get("/internal/pilotage/breakdown")
async def get_pilotage_breakdown(
    day: str = Query(alias="date"),
    dimension: str = Query(),
    metric: str = Query(),
    _claims: dict = Depends(require_pilotage),
    service: RideBreakdownService = Depends(ride_breakdown_service),
) -> dict:
    return await service.breakdown(day, dimension, metric)


@router.get("/internal/pilotage/health-summary")
async def get_pilotage_health_summary(
    request: Request,
    _claims: dict = Depends(require_pilotage),
) -> dict:
    db_ok = await database_ready()
    redis_pool = getattr(request.app.state, "redis", None)
    try:
        redis_ok = redis_pool is not None and bool(await redis_pool.ping())
    except Exception:
        redis_ok = False
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return {
        "contract_version": "pilotage.v1",
        "module": "diddigo",
        "status": "available" if db_ok and redis_ok else "degraded",
        "calculated_at": now,
        "freshness_window_seconds": 60,
        "components": [
            {"name": "database", "status": "available" if db_ok else "unavailable"},
            {"name": "redis", "status": "available" if redis_ok else "unavailable"},
        ],
        "sources": [{"module": "diddigo", "record_type": "health-summary"}],
    }
