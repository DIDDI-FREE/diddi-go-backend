from decimal import Decimal
from uuid import uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.domain.entities import DriverProfile, Ride, RideStatus, RideSupplement


class FakeRideRepo:
    def __init__(self, ride: Ride) -> None:
        self.ride = ride
        self.supplements: dict = {}

    async def find_by_id(self, ride_id):
        return self.ride if self.ride.id == ride_id else None

    async def save(self, ride):
        self.ride = ride
        return ride

    async def add_supplement(self, supplement):
        self.supplements[supplement.id] = supplement
        return supplement

    async def list_supplements(self, ride_id):
        return [item for item in self.supplements.values() if item.ride_id == ride_id]

    async def find_supplement_for_update(self, ride_id, supplement_id):
        item = self.supplements.get(supplement_id)
        return item if item is not None and item.ride_id == ride_id else None

    async def save_supplement(self, supplement):
        self.supplements[supplement.id] = supplement
        return supplement

    async def accepted_supplements_total(self, ride_id):
        return sum(
            (
                item.amount
                for item in self.supplements.values()
                if item.ride_id == ride_id and item.status == "accepted"
            ),
            Decimal("0"),
        )


class FakeDriverRepo:
    def __init__(self, profile: DriverProfile) -> None:
        self.profile = profile

    async def find_by_user_id(self, user_id):
        return self.profile if self.profile.user_id == user_id else None


def supplement_service():
    driver_user_id = uuid4()
    driver_id = uuid4()
    ride = Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        driver_id=driver_id,
        status=RideStatus.IN_PROGRESS,
        estimated_fare=Decimal("2500"),
    )
    repo = FakeRideRepo(ride)
    service = RideService(
        ride_repo=repo,
        routing=None,
        pricing_rules=None,
        driver_repo=FakeDriverRepo(
            DriverProfile(id=driver_id, user_id=driver_user_id, license_number="TEST"),
        ),
    )
    return service, repo, ride, driver_user_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("supplement_type", "expected"),
    [
        ("toll", 500),
        ("parking", 200),
        ("baggage_standard", 500),
        ("baggage_large", 1000),
    ],
)
async def test_driver_proposes_catalog_supplement_without_charging_it(supplement_type, expected):
    service, repo, ride, driver_user_id = supplement_service()

    result = await service.add_supplement(
        ride.id,
        actor_user_id=driver_user_id,
        actor_role="driver",
        supplement_type=supplement_type,
        amount=None,
    )

    assert result["amount"] == expected
    assert result["type"] == supplement_type
    assert result["status"] == "pending"
    assert repo.ride.supplements_total == Decimal("0")


@pytest.mark.asyncio
async def test_other_supplement_is_capped_at_one_thousand():
    service, _, ride, driver_user_id = supplement_service()

    with pytest.raises(ApiError) as error:
        await service.add_supplement(
            ride.id,
            actor_user_id=driver_user_id,
            actor_role="driver",
            supplement_type="other",
            amount=Decimal("1001"),
        )

    assert error.value.code == "INVALID_SUPPLEMENT_AMOUNT"


@pytest.mark.asyncio
async def test_passenger_can_list_and_accept_supplement_once():
    service, repo, ride, driver_user_id = supplement_service()
    proposed = await service.add_supplement(
        ride.id,
        actor_user_id=driver_user_id,
        actor_role="driver",
        supplement_type="toll",
        amount=None,
    )

    listed = await service.list_supplements(
        ride.id,
        actor_user_id=ride.passenger_user_id,
        actor_role="user",
    )
    assert listed["items"][0]["status"] == "pending"

    supplement_id = next(iter(repo.supplements))
    accepted = await service.decide_supplement(
        ride.id,
        supplement_id,
        actor_user_id=ride.passenger_user_id,
        actor_role="user",
        decision="accepted",
    )
    assert accepted["id"] == proposed["id"]
    assert accepted["status"] == "accepted"
    assert repo.ride.supplements_total == Decimal("500")

    replayed = await service.decide_supplement(
        ride.id,
        supplement_id,
        actor_user_id=ride.passenger_user_id,
        actor_role="user",
        decision="accepted",
    )
    assert replayed["status"] == "accepted"
    assert repo.ride.supplements_total == Decimal("500")


@pytest.mark.asyncio
async def test_disputed_supplement_is_not_billed_and_cannot_be_changed():
    service, repo, ride, driver_user_id = supplement_service()
    await service.add_supplement(
        ride.id,
        actor_user_id=driver_user_id,
        actor_role="driver",
        supplement_type="parking",
        amount=None,
    )
    supplement_id = next(iter(repo.supplements))

    disputed = await service.decide_supplement(
        ride.id,
        supplement_id,
        actor_user_id=ride.passenger_user_id,
        actor_role="user",
        decision="disputed",
    )
    assert disputed["status"] == "disputed"
    assert repo.ride.supplements_total == Decimal("0")

    with pytest.raises(ApiError) as error:
        await service.decide_supplement(
            ride.id,
            supplement_id,
            actor_user_id=ride.passenger_user_id,
            actor_role="user",
            decision="accepted",
        )
    assert error.value.code == "SUPPLEMENT_ALREADY_DECIDED"


@pytest.mark.asyncio
async def test_driver_cannot_decide_own_supplement():
    service, repo, ride, driver_user_id = supplement_service()
    supplement_id = uuid4()
    repo.supplements[supplement_id] = RideSupplement(
        id=supplement_id,
        ride_id=ride.id,
        amount=Decimal("500"),
        reason="toll",
    )
    with pytest.raises(ApiError) as error:
        await service.decide_supplement(
            ride.id,
            supplement_id,
            actor_user_id=driver_user_id,
            actor_role="driver",
            decision="accepted",
        )
    assert error.value.code == "RIDE_NOT_OWNED_BY_USER"
