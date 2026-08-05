import pytest

from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.infra.routing_client import RouteEstimateResult
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


class FakeRouting:
    async def estimate(self, origin, destination, profile="palh_vtc"):
        return RouteEstimateResult(
            distance_km=11.876,
            duration_seconds=983,
        )


class FakePricingRules:
    called = False

    async def find_active(self, city, vehicle_category):
        self.called = True
        return None


@pytest.mark.asyncio
async def test_pricing_uses_diddigo_policy_with_diddimap_distance():
    pricing_rules = FakePricingRules()
    service = RideService(
        ride_repo=None,
        routing=FakeRouting(),
        pricing_rules=pricing_rules,
    )

    result = await service.estimate_pricing(
        GeoPoint(lat=5.3599, lng=-4.0083),
        GeoPoint(lat=5.3167, lng=-4.0333),
        "standard",
    )

    assert result == {
        "estimated_fare": 3100,
        "currency": "XOF",
        "distance_km": 11.876,
        "duration_seconds": 983,
        "surge_multiplier": 1.0,
        "surge_cap": 1.6,
        "base_fare": 250,
        "distance_fare": 2850,
        "duration_fare": 0,
        "commission_rate": 0.08,
        "platform_commission": 248,
        "driver_payout_estimate": 2852,
    }
    assert pricing_rules.called is True
