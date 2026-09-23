import pytest

from app_base.main import app

pytestmark = pytest.mark.unit


def test_s2s_mutations_document_canonical_and_legacy_admin_actor_headers() -> None:
    schema = app.openapi()

    mutation_paths = (
        "/internal/v1/drivers/provision",
        "/internal/v1/drivers/{driver_id}/kyc/approve",
        "/internal/v1/drivers/{driver_id}/kyc/reject",
    )
    for path in mutation_paths:
        parameters = schema["paths"][path]["post"]["parameters"]
        canonical = next(parameter for parameter in parameters if parameter["name"] == "X-Backoffice-Actor")
        legacy = next(parameter for parameter in parameters if parameter["name"] == "X-User-ID")
        assert canonical["in"] == legacy["in"] == "header"
        assert canonical["required"] is False
        assert legacy["required"] is False
        assert legacy["deprecated"] is True
