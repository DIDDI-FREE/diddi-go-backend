from __future__ import annotations

import pytest
from pydantic import ValidationError

from app_base.modules.ride.presentation.schemas import PricingEstimateRequest, RideCreateRequest


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lat", -90.0001),
        ("lat", 90.0001),
        ("lng", -180.0001),
        ("lng", 180.0001),
    ],
)
@pytest.mark.parametrize("schema", [PricingEstimateRequest, RideCreateRequest])
def test_ride_coordinates_are_rejected_before_diddimap(schema, field: str, value: float) -> None:
    pickup = {"lat": 5.3599, "lng": -4.0083}
    pickup[field] = value

    with pytest.raises(ValidationError):
        schema.model_validate(
            {
                "pickup": pickup,
                "dropoff": {"lat": 5.3167, "lng": -4.0333},
            }
        )
