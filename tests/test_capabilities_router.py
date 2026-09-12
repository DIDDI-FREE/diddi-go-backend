from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app_base.core.auth_deps import get_current_active_user
from app_base.core.deps import driver_service, scoring_service
from app_base.main import app

pytestmark = pytest.mark.unit


class FakeDriverCapabilitiesService:
    async def get_capabilities(self, user_id, *, identity_role: str, identity_status: str) -> dict:
        return {
            "user_id": str(user_id),
            "identity": {"role": identity_role, "status": identity_status},
            "service": "diddigo",
            "consumer": {"type": "passenger", "enabled": True, "status": "active", "blocking_reasons": []},
            "professional_profiles": [
                {
                    "type": "driver",
                    "exists": False,
                    "status": "not_created",
                    "verification_status": "not_created",
                    "can_go_online": False,
                    "blocking_reasons": ["driver_profile_not_created"],
                    "driver_profile_id": None,
                    "vehicle": None,
                    "score": None,
                }
            ],
            "capabilities": [
                {
                    "service": "diddigo",
                    "type": "passenger",
                    "status": "active",
                    "enabled": True,
                    "blocking_reasons": [],
                },
                {
                    "service": "diddigo",
                    "type": "driver",
                    "status": "not_created",
                    "enabled": False,
                    "blocking_reasons": ["driver_profile_not_created"],
                },
            ],
        }


class FakeScoringService:
    async def get_my_scores(self, user_id) -> dict:
        return {
            "user_id": str(user_id),
            "service": "diddigo",
            "passenger_score": {
                "subject_type": "passenger",
                "subject_id": str(user_id),
                "score_value": 4.8,
                "score_level": "new",
                "score_status": "insufficient_data",
                "reason_codes": ["insufficient_data"],
                "last_calculated_at": "2026-09-12T00:00:00Z",
                "sample_size": 1,
                "metrics": {},
            },
            "driver_score": None,
        }


def test_me_capabilities_route_returns_service_payload() -> None:
    user_id = uuid4()

    async def fake_current_user():
        return SimpleNamespace(id=user_id, role="user", status="active")

    async def fake_driver_service():
        return FakeDriverCapabilitiesService()

    app.dependency_overrides[get_current_active_user] = fake_current_user
    app.dependency_overrides[driver_service] = fake_driver_service
    try:
        response = TestClient(app).get("/v1/me/capabilities")
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)
        app.dependency_overrides.pop(driver_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(user_id)
    assert body["service"] == "diddigo"
    assert body["capabilities"][0]["type"] == "passenger"
    assert body["capabilities"][1]["blocking_reasons"] == ["driver_profile_not_created"]


def test_me_scores_route_returns_service_payload() -> None:
    user_id = uuid4()

    async def fake_current_user():
        return SimpleNamespace(id=user_id, role="user", status="active")

    async def fake_scoring_service():
        return FakeScoringService()

    app.dependency_overrides[get_current_active_user] = fake_current_user
    app.dependency_overrides[scoring_service] = fake_scoring_service
    try:
        response = TestClient(app).get("/v1/me/scores")
    finally:
        app.dependency_overrides.pop(get_current_active_user, None)
        app.dependency_overrides.pop(scoring_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(user_id)
    assert body["passenger_score"]["subject_type"] == "passenger"
    assert body["driver_score"] is None
