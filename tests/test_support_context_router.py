from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app_base.core.database import get_session
from app_base.core.errors import ApiError
from app_base.main import app
from app_base.modules.ride.presentation.support_context_router import require_diddisupport

RIDE_ID = UUID("11111111-1111-1111-1111-111111111111")
PASSENGER_ID = UUID("22222222-2222-2222-2222-222222222222")
DRIVER_USER_ID = UUID("33333333-3333-3333-3333-333333333333")


def _headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer service-token",
        "X-Client-ID": "diddisupport-staging-diddigo",
        "X-Request-ID": "support-context-contract-test",
        "X-Support-Context-Scope": "diddigo:support-context:read",
    }


@pytest.fixture
def support_client(monkeypatch):
    async def allow_service():
        return {"sub": "service:diddisupport"}

    async def fake_session():
        return object()

    async def fake_resolve(self, ride_id):
        assert ride_id == RIDE_ID
        at = datetime(2026, 10, 20, 11, 0, tzinfo=UTC)
        return SimpleNamespace(
            ride_id=RIDE_ID, status="completed", completion_reason="normal", cancellation_reason=None,
            fare_amount=Decimal("3700"), currency="XOF", payment_method="mobile_money",
            participants=[
                SimpleNamespace(user_id=PASSENGER_ID, role="passenger"),
                SimpleNamespace(user_id=DRIVER_USER_ID, role="driver"),
            ],
            requested_at=at, matched_at=at, arrived_at=at, started_at=at,
            completed_at=at, cancelled_at=None, as_of=at,
        )

    monkeypatch.setattr(
        "app_base.modules.ride.presentation.support_context_router.RideSupportContextResolver.resolve",
        fake_resolve,
    )
    app.dependency_overrides[require_diddisupport] = allow_service
    app.dependency_overrides[get_session] = fake_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(require_diddisupport, None)
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.unit
def test_support_context_returns_versioned_redacted_contract(support_client) -> None:
    response = support_client.get(f"/internal/v1/support/ride/{RIDE_ID}/context", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["protocol"] == "diddi.context.v1"
    assert body["origin_service"] == "diddigo"
    assert body["resource_type"] == "ride"
    assert body["resource_id"] == str(RIDE_ID)
    assert body["data"]["status"] == "completed"
    assert body["data"]["fare_amount"] == "3700"
    assert body["data"]["participants"] == [
        {"user_id": str(PASSENGER_ID), "role": "passenger"},
        {"user_id": str(DRIVER_USER_ID), "role": "driver"},
    ]
    assert "participants.phone_e164" in body["redacted_fields"]
    assert "locations.pickup" in body["redacted_fields"]
    assert "phone" not in str(body["data"])
    assert response.headers["X-Request-ID"] == "support-context-contract-test"


@pytest.mark.unit
def test_support_context_requires_service_authentication() -> None:
    response = TestClient(app).get(f"/internal/v1/support/ride/{RIDE_ID}/context")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_MISSING"


@pytest.mark.unit
def test_support_context_rejects_missing_protocol_scope_header(support_client) -> None:
    headers = _headers()
    headers.pop("X-Support-Context-Scope")

    response = support_client.get(f"/internal/v1/support/ride/{RIDE_ID}/context", headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SERVICE_SCOPE_HEADER_INVALID"


@pytest.mark.unit
def test_support_context_returns_not_found_for_unknown_ride(support_client, monkeypatch) -> None:
    async def unknown_ride(self, ride_id):
        raise ApiError(404, "RIDE_NOT_FOUND", "Course introuvable.")

    monkeypatch.setattr(
        "app_base.modules.ride.presentation.support_context_router.RideSupportContextResolver.resolve",
        unknown_ride,
    )
    response = support_client.get(f"/internal/v1/support/ride/{RIDE_ID}/context", headers=_headers())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RIDE_NOT_FOUND"


@pytest.mark.unit
def test_support_context_rejects_service_token_without_scope(monkeypatch) -> None:
    def reject_scope(*_args, **_kwargs):
        raise ApiError(403, "SERVICE_SCOPE_INVALID", "Le token ne contient pas le scope requis.")

    monkeypatch.setattr("app_base.core.auth_deps.decode_identity_service_token", reject_scope)
    response = TestClient(app).get(f"/internal/v1/support/ride/{RIDE_ID}/context", headers=_headers())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SERVICE_SCOPE_INVALID"


@pytest.mark.unit
def test_support_context_returns_service_unavailable_when_jwks_is_unavailable(monkeypatch) -> None:
    def unavailable(*_args, **_kwargs):
        raise ApiError(503, "SERVICE_JWKS_UNAVAILABLE", "JWKS temporairement indisponible.")

    monkeypatch.setattr("app_base.core.auth_deps.decode_identity_service_token", unavailable)
    response = TestClient(app).get(f"/internal/v1/support/ride/{RIDE_ID}/context", headers=_headers())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_JWKS_UNAVAILABLE"


@pytest.mark.unit
def test_support_context_openapi_documents_contract_and_headers() -> None:
    schema = app.openapi()
    operation = schema["paths"]["/internal/v1/support/ride/{ride_id}/context"]["get"]
    parameters = {item["name"]: item for item in operation["parameters"]}

    assert parameters["X-Support-Context-Scope"]["in"] == "header"
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/SupportRideContextResponse"
    )
