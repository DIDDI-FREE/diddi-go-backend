from app_base.main import app
from app_base.modules.ride.application.services import RideService


def test_supplement_catalog_and_other_label_are_typed_in_openapi() -> None:
    schema = app.openapi()
    assert "/v1/rides/config/supplements" in schema["paths"]
    request = schema["components"]["schemas"]["RideSupplementCreateRequest"]
    assert "custom_label" in request["properties"]
    response = schema["components"]["schemas"]["RideSupplementResponse"]
    assert "custom_label" in response["properties"]


def test_supplement_catalog_is_server_controlled() -> None:
    service = object.__new__(RideService)
    catalog = service.get_supplement_catalog()
    by_type = {item["type"]: item for item in catalog["items"]}
    assert catalog["currency"] == "XOF"
    assert by_type["toll"]["amount_xof"] == 500
    assert by_type["other"]["requires_custom_label"] is True
    assert by_type["other"]["maximum_amount_xof"] == 1000
