import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app_base.main import app

pytestmark = pytest.mark.unit


def test_file_based_backoffice_manifest_declares_supported_s2s_commands() -> None:
    path = Path(__file__).parents[1] / "manifests" / "manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["contract_version"] == "backoffice.v1"
    module = payload["modules"][0]
    assert module["module"] == "diddigo"
    assert {command["name"] for command in module["commands"]} == {
        "approve_driver_kyc",
        "reject_driver_kyc",
        "provision_driver",
    }
    assert all(command.get("service_scope") for command in module["commands"])


def test_manifest_is_not_exposed_as_an_http_endpoint() -> None:
    response = TestClient(app).get("/internal/backoffice/v1/manifest")

    assert response.status_code == 404
