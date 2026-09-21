from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app_base.core.auth_deps import require_role
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.observability.application.services import OperationalLogSearchService
from app_base.modules.observability.infra.loki import LokiOperationalLogRepository

router = APIRouter(prefix="/admin/logs", tags=["admin-observability"])


def operational_log_search_service() -> OperationalLogSearchService:
    return OperationalLogSearchService(LokiOperationalLogRepository())


@router.get("/rides/{ride_id}")
async def search_ride_logs(
    ride_id: UUID,
    start: datetime | None = Query(default=None, alias="from"),
    end: datetime | None = Query(default=None, alias="to"),
    level: str | None = Query(default=None, pattern="^(?i:debug|info|warning|error|critical)$"),
    limit: int = Query(default=100, ge=1, le=500),
    cursor: str | None = None,
    _admin: UserModel = Depends(require_role("admin")),
    service: OperationalLogSearchService = Depends(operational_log_search_service),
) -> dict:
    return await service.search(
        field="ride_id",
        value=str(ride_id),
        start=start,
        end=end,
        level=level,
        limit=limit,
        cursor=cursor,
    )


@router.get("/drivers/{driver_id}")
async def search_driver_logs(
    driver_id: UUID,
    start: datetime | None = Query(default=None, alias="from"),
    end: datetime | None = Query(default=None, alias="to"),
    level: str | None = Query(default=None, pattern="^(?i:debug|info|warning|error|critical)$"),
    limit: int = Query(default=100, ge=1, le=500),
    cursor: str | None = None,
    _admin: UserModel = Depends(require_role("admin")),
    service: OperationalLogSearchService = Depends(operational_log_search_service),
) -> dict:
    return await service.search(
        field="driver_id",
        value=str(driver_id),
        start=start,
        end=end,
        level=level,
        limit=limit,
        cursor=cursor,
    )
