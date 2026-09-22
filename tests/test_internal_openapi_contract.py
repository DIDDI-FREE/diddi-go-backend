import pytest

from app_base.main import app

pytestmark = pytest.mark.unit


def test_s2s_mutations_document_required_admin_actor_header() -> None:
    schema = app.openapi()

    mutation_paths = (
        "/internal/v1/drivers/provision",
        "/internal/v1/drivers/{driver_id}/kyc/approve",
        "/internal/v1/drivers/{driver_id}/kyc/reject",
    )
    for path in mutation_paths:
        parameters = schema["paths"][path]["post"]["parameters"]
        actor_header = next(parameter for parameter in parameters if parameter["name"] == "X-User-ID")
        assert actor_header["in"] == "header"
        assert actor_header["required"] is True
