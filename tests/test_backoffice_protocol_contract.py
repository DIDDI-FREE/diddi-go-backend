from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app_base.core.errors import ApiError
from app_base.main import app
from app_base.modules.ride.presentation.backoffice_contract_router import require_manifest_read

pytestmark = pytest.mark.unit


def test_backoffice_manifest_is_scoped_and_machine_readable() -> None:
    app.dependency_overrides[require_manifest_read] = lambda: {"sub": "service:backoffice"}
    try:
        response = TestClient(app).get("/internal/backoffice/v1/manifest")
    finally:
        app.dependency_overrides.pop(require_manifest_read, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_version"] == "backoffice.v1"
    assert payload["module"] == "diddigo"
    assert {command["name"] for command in payload["commands"]} == {
        "approve_driver_kyc",
        "reject_driver_kyc",
        "provision_driver",
    }


def test_internal_error_exposes_request_id_at_protocol_level() -> None:
    request_id = str(uuid4())

    async def reject():
        raise ApiError(403, "permission_denied", "Required scope is missing")

    app.dependency_overrides[require_manifest_read] = reject
    try:
        response = TestClient(app).get(
            "/internal/backoffice/v1/manifest",
            headers={"X-Request-ID": request_id},
        )
    finally:
        app.dependency_overrides.pop(require_manifest_read, None)

    assert response.status_code == 403
    assert response.json()["error"]["request_id"] == request_id
