from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    PaymentMethod,
    Ride,
    RideRoutePoint,
    RideStatus,
    VehicleCategory,
)
from app_base.modules.ride.infra.routing_client import RouteEstimateResult
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


class FakeRouting:
    def __init__(self):
        self.trace_points = []

    async def estimate(self, origin, destination, profile="palh_vtc"):
        return RouteEstimateResult(
            distance_km=11.876,
            duration_seconds=983,
        )

    async def geocode(self, query, bias=None, limit=None):
        return []

    async def start_trace(
        self,
        *,
        start,
        end,
        planned_distance_km=None,
        planned_duration_seconds=None,
        profile="palh_vtc",
    ):
        return "trace-123"

    async def append_trace_positions(self, trace_id, points):
        self.trace_points.extend(points)

    async def finish_trace(self, trace_id, *, finished_at):
        return None

    async def analyze_trace(self, trace_id):
        return SimpleNamespace(actual_distance_km=Decimal("12.5"), actual_duration_seconds=900)


class FakeRideRepo:
    def __init__(self, points):
        self._points = points

    async def list_route_points(self, ride_id):
        return self._points


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
        "comfort_multiplier": 1.0,
        "base_fare": 250,
        "distance_fare": 2850,
        "duration_fare": 0,
        "commission_rate": 0.08,
        "platform_commission": 248,
        "driver_payout_estimate": 2852,
    }
    assert pricing_rules.called is True


@pytest.mark.asyncio
async def test_pricing_increases_with_comfort_level():
    service = RideService(
        ride_repo=None,
        routing=FakeRouting(),
        pricing_rules=FakePricingRules(),
    )

    standard = await service.estimate_pricing(
        GeoPoint(lat=5.3599, lng=-4.0083),
        GeoPoint(lat=5.3167, lng=-4.0333),
        "standard",
        "standard",
    )
    premium = await service.estimate_pricing(
        GeoPoint(lat=5.3599, lng=-4.0083),
        GeoPoint(lat=5.3167, lng=-4.0333),
        "standard",
        "premium",
    )

    assert premium["comfort_multiplier"] == 1.3
    assert premium["estimated_fare"] > standard["estimated_fare"]


@pytest.mark.asyncio
async def test_completed_ride_pricing_uses_diddimap_trace_metrics():
    ride_id = uuid4()
    points = [
        RideRoutePoint(
            ride_id=ride_id,
            location=GeoPoint(lat=5.352, lng=-3.997),
            recorded_at=datetime.now(UTC),
            speed_kmh=Decimal("36"),
            accuracy_m=Decimal("8"),
        )
    ]
    routing = FakeRouting()
    service = RideService(
        ride_repo=FakeRideRepo(points),
        routing=routing,
        pricing_rules=FakePricingRules(),
    )
    ride = Ride(
        id=ride_id,
        passenger_user_id=uuid4(),
        status=RideStatus.IN_PROGRESS,
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.STANDARD,
        pickup_location=GeoPoint(lat=5.3599, lng=-4.0083),
        dropoff_location=GeoPoint(lat=5.3167, lng=-4.0333),
        estimated_fare=Decimal("3100"),
        distance_km=Decimal("11.876"),
        duration_seconds=983,
        base_fare=Decimal("250"),
        distance_fare=Decimal("2850"),
        duration_fare=Decimal("0"),
        payment_method=PaymentMethod.CASH,
    )

    await service._apply_actual_pricing_if_possible(ride)

    assert ride.map_trace_id == "trace-123"
    assert ride.actual_distance_km == Decimal("12.5")
    assert ride.actual_duration_seconds == 900
    assert ride.final_fare == Decimal("3250")
    assert ride.platform_commission == Decimal("260")
    assert ride.driver_payout_estimate == Decimal("2990")
    assert routing.trace_points == points
