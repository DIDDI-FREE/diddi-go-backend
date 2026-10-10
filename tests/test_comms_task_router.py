from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app_base.core.database import get_session
from app_base.main import app
from app_base.modules.ride.presentation.comms_task_router import require_diddicomms

RIDE_ID = UUID("11111111-1111-1111-1111-111111111111")
PASSENGER_ID = UUID("22222222-2222-2222-2222-222222222222")
DRIVER_USER_ID = UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
def comms_client(monkeypatch):
    async def allow_service():
        return {"sub": "service:diddicomms"}

    async def fake_session():
        return object()

    async def fake_resolve(self, *, task_type, task_id):
        assert task_type == "ride"
        assert task_id == RIDE_ID
        return SimpleNamespace(
            owner_service="diddigo",
            task_type="ride",
            task_id=RIDE_ID,
            state="driver_assigned",
            version=1791633600,
            participants=[
                SimpleNamespace(user_id=PASSENGER_ID, role="passenger", phone_e164="+237600000001"),
                SimpleNamespace(user_id=DRIVER_USER_ID, role="driver", phone_e164="+237600000002"),
            ],
            messaging_allowed=True,
            calling_allowed=True,
            closes_at=datetime(2026, 10, 10, 13, 0, tzinfo=UTC),
        )

    monkeypatch.setattr(
        "app_base.modules.ride.presentation.comms_task_router.RideCommsTaskResolver.resolve",
        fake_resolve,
    )
    app.dependency_overrides[require_diddicomms] = allow_service
    app.dependency_overrides[get_session] = fake_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(require_diddicomms, None)
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.unit
def test_comms_task_route_returns_projection(comms_client) -> None:
    response = comms_client.get(f"/internal/v1/comms/tasks/ride/{RIDE_ID}")

    assert response.status_code == 200
    assert response.json() == {
        "task": {
            "owner_service": "diddigo",
            "task_type": "ride",
            "task_id": str(RIDE_ID),
        },
        "state": "driver_assigned",
        "version": 1791633600,
        "participants": [
            {"user_id": str(PASSENGER_ID), "role": "passenger", "phone_e164": "+237600000001"},
            {"user_id": str(DRIVER_USER_ID), "role": "driver", "phone_e164": "+237600000002"},
        ],
        "messaging_allowed": True,
        "calling_allowed": True,
        "closes_at": "2026-10-10T13:00:00Z",
    }


@pytest.mark.unit
def test_comms_task_route_requires_service_authentication() -> None:
    response = TestClient(app).get(f"/internal/v1/comms/tasks/ride/{RIDE_ID}")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_MISSING"


@pytest.mark.unit
def test_comms_task_route_rejects_another_service_client() -> None:
    response = TestClient(app).get(
        f"/internal/v1/comms/tasks/ride/{RIDE_ID}",
        headers={
            "Authorization": "Bearer not-decoded-because-client-is-forbidden",
            "X-Client-ID": "another-staging-diddigo",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SERVICE_CLIENT_FORBIDDEN"
