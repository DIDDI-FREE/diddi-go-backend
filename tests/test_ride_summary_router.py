import pytest
from fastapi.testclient import TestClient

from app_base.core.deps import ride_summary_service
from app_base.core.errors import ApiError
from app_base.main import app
from app_base.modules.ride.presentation.summary_router import require_pilotage


class FakeSummaryService:
    async def daily_summary(self, day: str) -> dict:
        return {
            "module": "diddigo",
            "date": day,
            "timezone": "Africa/Abidjan",
            "rides_requested": 1,
            "rides_completed": 1,
            "completed_fare_total_xof": 3500,
            "calculated_at": "2026-09-19T00:00:00Z",
        }


@pytest.fixture
def summary_client():
    async def allow_service():
        return {"sub": "service:pilotage"}

    app.dependency_overrides[require_pilotage] = allow_service
    app.dependency_overrides[ride_summary_service] = lambda: FakeSummaryService()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(require_pilotage, None)
        app.dependency_overrides.pop(ride_summary_service, None)


@pytest.mark.unit
def test_ride_summary_route_returns_internal_payload(summary_client) -> None:
    response = summary_client.get("/internal/v1/ride-summary?date=2026-09-19")

    assert response.status_code == 200
    assert response.json()["completed_fare_total_xof"] == 3500


@pytest.mark.unit
def test_ride_summary_route_requires_service_authentication() -> None:
    response = TestClient(app).get("/internal/v1/ride-summary?date=2026-09-19")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_MISSING"


@pytest.mark.unit
def test_ride_summary_route_rejects_forbidden_service(summary_client) -> None:
    async def deny_service():
        raise ApiError(403, "SERVICE_SCOPE_INVALID", "Scopes insuffisants pour cette operation.")

    app.dependency_overrides[require_pilotage] = deny_service
    try:
        response = summary_client.get("/internal/v1/ride-summary?date=2026-09-19")
    finally:
        app.dependency_overrides[require_pilotage] = lambda: {"sub": "service:pilotage"}

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SERVICE_SCOPE_INVALID"
