from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app_base.core.deps import scoring_service
from app_base.main import app
from app_base.modules.ride.presentation.score_contract_router import require_diddifreepro

USER_ID = UUID("11111111-1111-1111-1111-111111111111")
RIDE_ID = UUID("22222222-2222-2222-2222-222222222222")

pytestmark = pytest.mark.unit


class FakeScoringService:
    async def get_my_scores(self, user_id: UUID) -> dict:
        assert user_id == USER_ID
        return {
            "passenger_score": {
                "subject_type": "passenger", "subject_id": str(USER_ID), "score_value": 4.0,
                "score_level": "new", "score_status": "insufficient_data", "sample_size": 0,
                "reason_codes": ["no_activity"], "last_calculated_at": "2026-10-20T10:00:00Z",
            },
            "driver_score": {
                "subject_type": "driver", "subject_id": "33333333-3333-3333-3333-333333333333", "score_value": 4.7,
                "score_level": "excellent", "score_status": "stable", "sample_size": 7,
                "reason_codes": ["good_ratings"], "last_calculated_at": "2026-10-20T10:00:00Z",
            },
        }

    async def get_ride_score_for_internal(self, ride_id: UUID) -> dict:
        assert ride_id == RIDE_ID
        return {
            "ride_id": str(RIDE_ID), "score_value": 4.5, "score_level": "good",
            "score_status": "stable", "sample_size": 2, "reason_codes": ["good_ratings"],
            "last_calculated_at": "2026-10-20T10:00:00Z",
        }


@pytest.fixture
def score_client():
    async def allow_service():
        return {"sub": "service:diddifreepro"}

    async def fake_service():
        return FakeScoringService()

    app.dependency_overrides[require_diddifreepro] = allow_service
    app.dependency_overrides[scoring_service] = fake_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(require_diddifreepro, None)
        app.dependency_overrides.pop(scoring_service, None)


@pytest.mark.unit
def test_service_can_read_a_user_score_collection(score_client) -> None:
    response = score_client.get(f"/internal/v1/scores/users/{USER_ID}")

    assert response.status_code == 200
    scores = response.json()["scores"]
    assert len(scores) == 2
    assert scores[0]["contract_version"] == "diddi.score.v1"
    assert scores[0]["score"]["normalized_level"] == "unknown"
    assert scores[1]["score"]["normalized_value"] == 94.0
    assert scores[1]["score"]["calculation_version"] == "diddigo_reliability_v1"


@pytest.mark.unit
def test_service_can_read_a_ride_quality_score(score_client) -> None:
    response = score_client.get(f"/internal/v1/scores/rides/{RIDE_ID}")

    assert response.status_code == 200
    assert response.json()["kind"] == "quality"
    assert response.json()["user_id"] is None
    assert response.json()["score"]["calculation_version"] == "diddigo_trip_quality_v1"


@pytest.mark.unit
def test_score_contract_route_requires_service_authentication() -> None:
    response = TestClient(app).get(f"/internal/v1/scores/users/{USER_ID}")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_MISSING"


@pytest.mark.unit
def test_score_contract_route_rejects_another_service_client() -> None:
    response = TestClient(app).get(
        f"/internal/v1/scores/users/{USER_ID}",
        headers={
            "Authorization": "Bearer not-decoded-because-client-is-forbidden",
            "X-Client-ID": "another-staging-diddigo",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SERVICE_CLIENT_FORBIDDEN"


@pytest.mark.unit
def test_score_contract_openapi_is_typed() -> None:
    schema = app.openapi()
    user_operation = schema["paths"]["/internal/v1/scores/users/{user_id}"]["get"]
    ride_operation = schema["paths"]["/internal/v1/scores/rides/{ride_id}"]["get"]

    assert user_operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/DiddiScoreCollectionResponse"
    )
    assert ride_operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/DiddiScoreResponse"
    )
