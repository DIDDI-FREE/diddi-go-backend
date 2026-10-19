import pytest
from pydantic import ValidationError

from app_base.main import app
from app_base.modules.ride.presentation.driver_schemas import VehicleCreateRequest, VehicleUpdateRequest

pytestmark = pytest.mark.unit


def test_passenger_debt_routes_are_exposed_in_openapi() -> None:
    schema = app.openapi()
    paths = schema["paths"]

    assert "/v1/passenger/debts" in paths
    assert "/v1/passenger/debts/{debt_id}/mobile-money/prepare" in paths
    assert "/v1/passenger/debts/{debt_id}/cash-request" in paths
    assert "/v1/passenger/debts/{debt_id}/confirm-cash" in paths
    assert paths["/v1/passenger/debts"]["get"]["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("PassengerDebtListResponse")


@pytest.mark.parametrize("schema", [VehicleCreateRequest, VehicleUpdateRequest])
def test_vehicle_make_and_model_are_required(schema) -> None:
    with pytest.raises(ValidationError):
        schema(plate_number="AB-123-CD")

    payload = schema(plate_number="AB-123-CD", make="Toyota", model="Corolla")
    assert payload.make == "Toyota"
    assert payload.model == "Corolla"
