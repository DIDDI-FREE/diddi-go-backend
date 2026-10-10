from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.infra.routing_client import RouteEstimateResult
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


class FakeRouting:
    async def estimate(self, origin, destination, profile="palh_vtc"):
        return RouteEstimateResult(distance_km=4.5, duration_seconds=600)


class FakePricingRules:
    async def find_active(self, city, vehicle_category):
        return None


class FakeQuoteRepository:
    def __init__(self):
        self.quotes = {}

    async def save(self, quote):
        self.quotes[quote.id] = quote
        return quote

    async def find_by_id(self, quote_id):
        return self.quotes.get(quote_id)

    async def consume(self, quote, *, ride_id, consumed_at):
        quote.ride_id = ride_id
        quote.consumed_at = consumed_at


class FakeRideRepository:
    def __init__(self):
        self.rides = {}

    async def has_active_ride(self, passenger_user_id):
        return False

    async def save(self, ride):
        self.rides[ride.id] = ride
        return ride

    async def record_status_transition(self, transition):
        return None


def service_with_repositories():
    quotes = FakeQuoteRepository()
    rides = FakeRideRepository()
    service = RideService(
        ride_repo=rides,
        routing=FakeRouting(),
        pricing_rules=FakePricingRules(),
        quote_repo=quotes,
    )
    return service, quotes, rides


@pytest.mark.asyncio
async def test_quote_is_persisted_and_snapshotted_into_ride():
    service, quotes, rides = service_with_repositories()
    passenger_id = uuid4()
    result = await service.create_quote(
        passenger_user_id=passenger_id,
        pickup=GeoPoint(lat=5.35, lng=-4.01),
        pickup_address="Cocody",
        dropoff=GeoPoint(lat=5.32, lng=-4.02),
        dropoff_address="Plateau",
        vehicle_category="standard",
        comfort_level="premium",
    )

    quote = next(iter(quotes.quotes.values()))
    assert result["quote_id"] == str(quote.id)
    assert result["expires_at"]
    assert result["tariff_version"]

    ride = await service.request_ride(
        passenger_user_id=passenger_id,
        quote_id=quote.id,
        payment_method="cash",
        scheduled_at=None,
    )

    assert rides.rides[ride.id] is ride
    assert ride.quote_id == quote.id
    assert ride.estimated_fare == quote.estimated_fare
    assert ride.comfort_level == quote.comfort_level
    assert quote.ride_id == ride.id
    assert quote.consumed_at is not None


@pytest.mark.asyncio
async def test_expired_quote_is_rejected():
    service, quotes, _rides = service_with_repositories()
    passenger_id = uuid4()
    result = await service.create_quote(
        passenger_user_id=passenger_id,
        pickup=GeoPoint(lat=5.35, lng=-4.01),
        pickup_address=None,
        dropoff=GeoPoint(lat=5.32, lng=-4.02),
        dropoff_address=None,
        vehicle_category="standard",
        comfort_level="standard",
    )
    quote = quotes.quotes[next(key for key in quotes.quotes if str(key) == result["quote_id"])]
    quote.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    with pytest.raises(ApiError) as exc_info:
        await service.request_ride(
            passenger_user_id=passenger_id,
            quote_id=quote.id,
            payment_method="cash",
            scheduled_at=None,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "QUOTE_EXPIRED"


@pytest.mark.asyncio
async def test_quote_cannot_be_reused():
    service, quotes, _rides = service_with_repositories()
    passenger_id = uuid4()
    await service.create_quote(
        passenger_user_id=passenger_id,
        pickup=GeoPoint(lat=5.35, lng=-4.01),
        pickup_address=None,
        dropoff=GeoPoint(lat=5.32, lng=-4.02),
        dropoff_address=None,
        vehicle_category="standard",
        comfort_level="standard",
    )
    quote = next(iter(quotes.quotes.values()))
    quote.consumed_at = datetime.now(UTC)

    with pytest.raises(ApiError) as exc_info:
        await service.request_ride(
            passenger_user_id=passenger_id,
            quote_id=quote.id,
            payment_method="cash",
            scheduled_at=None,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "QUOTE_ALREADY_USED"


@pytest.mark.asyncio
async def test_quote_is_private_to_its_passenger():
    service, quotes, _rides = service_with_repositories()
    await service.create_quote(
        passenger_user_id=uuid4(),
        pickup=GeoPoint(lat=5.35, lng=-4.01),
        pickup_address=None,
        dropoff=GeoPoint(lat=5.32, lng=-4.02),
        dropoff_address=None,
        vehicle_category="standard",
        comfort_level="standard",
    )
    quote = next(iter(quotes.quotes.values()))

    with pytest.raises(ApiError) as exc_info:
        await service.request_ride(
            passenger_user_id=uuid4(),
            quote_id=quote.id,
            payment_method="cash",
            scheduled_at=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "QUOTE_NOT_FOUND"
