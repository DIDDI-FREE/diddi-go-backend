import pytest

from app_base.main import app

pytestmark = pytest.mark.unit


def test_s2s_mutations_document_canonical_actor_header_only() -> None:
    schema = app.openapi()

    mutation_paths = (
        "/internal/v1/drivers/provision",
        "/internal/v1/drivers/{driver_id}/kyc/approve",
        "/internal/v1/drivers/{driver_id}/kyc/reject",
    )
    for path in mutation_paths:
        parameters = schema["paths"][path]["post"]["parameters"]
        names = {parameter["name"] for parameter in parameters}
        assert "X-Backoffice-Actor" in names
        # Legacy alias retired after the Backoffice migration (SCRUM-485).
        assert "X-User-ID" not in names
        canonical = next(parameter for parameter in parameters if parameter["name"] == "X-Backoffice-Actor")
        assert canonical["in"] == "header"
