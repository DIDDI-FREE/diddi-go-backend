from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.emergency_contact_service import EmergencyContactService
from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.domain.entities import EmergencyContact, Ride
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


USER_ID = uuid4()
RIDE_ID = uuid4()


class FakeEmergencyContactRepo:
    def __init__(self, contact: EmergencyContact | None = None) -> None:
        self.contact = contact
        self.deleted = False

    async def find_by_user_id(self, user_id: UUID) -> EmergencyContact | None:
        return self.contact if self.contact and self.contact.user_id == user_id else None

    async def save(self, contact: EmergencyContact) -> EmergencyContact:
        self.contact = contact
        return contact

    async def delete_for_user(self, user_id: UUID) -> bool:
        if self.contact is None or self.contact.user_id != user_id:
            return False
        self.contact = None
        self.deleted = True
        return True


class FakeRideRepo:
    def __init__(self, ride: Ride) -> None:
        self.ride = ride
        self.saved = False

    async def find_by_id(self, ride_id: UUID) -> Ride | None:
        return self.ride if ride_id == self.ride.id else None

    async def save(self, ride: Ride) -> Ride:
        self.ride = ride
        self.saved = True
        return ride


class FakeNotifier:
    def __init__(self) -> None:
        self.contact: EmergencyContact | None = None

    async def notify(self, **kwargs) -> list[dict]:
        self.contact = kwargs["contact"]
        return [{"target": "support", "channel": "email", "status": "skipped"}]


class FakeRouting:
    pass


class FakePricingRules:
    pass


@pytest.mark.asyncio
async def test_emergency_contact_requires_phone_or_email() -> None:
    service = EmergencyContactService(contacts=FakeEmergencyContactRepo())

    with pytest.raises(ApiError) as exc_info:
        await service.upsert_for_user(
            user_id=USER_ID,
            contact_name="Maman",
            phone=" ",
            email=None,
            relationship="famille",
        )

    assert exc_info.value.code == "EMERGENCY_CONTACT_REQUIRED"


@pytest.mark.asyncio
async def test_emergency_contact_upsert_and_delete() -> None:
    repo = FakeEmergencyContactRepo()
    service = EmergencyContactService(contacts=repo)

    saved = await service.upsert_for_user(
        user_id=USER_ID,
        contact_name="Support famille",
        phone="+2250700000000",
        email="family@example.com",
        relationship="famille",
    )
    deleted = await service.delete_for_user(USER_ID)

    assert saved["phone"] == "+2250700000000"
    assert deleted == {"status": "deleted"}
    assert repo.deleted is True


@pytest.mark.asyncio
async def test_ride_emergency_notifies_with_stored_contact() -> None:
    contact = EmergencyContact(
        id=uuid4(),
        user_id=USER_ID,
        contact_name="Famille",
        phone="+2250700000000",
        email="family@example.com",
    )
    ride = Ride(
        id=RIDE_ID,
        passenger_user_id=USER_ID,
        pickup_location=GeoPoint(lat=5.35, lng=-4.0),
        dropoff_location=GeoPoint(lat=5.36, lng=-3.99),
        requested_at=datetime.now(UTC),
    )
    notifier = FakeNotifier()
    service = RideService(
        ride_repo=FakeRideRepo(ride),
        routing=FakeRouting(),
        pricing_rules=FakePricingRules(),
        emergency_contact_repo=FakeEmergencyContactRepo(contact),
        emergency_notifications=notifier,
    )

    result = await service.request_emergency(
        RIDE_ID,
        actor_user_id=USER_ID,
        actor_role="user",
        note="Besoin assistance",
    )

    assert result["status"] == "open"
    assert result["notifications"][0]["target"] == "support"
    assert notifier.contact == contact


@pytest.mark.asyncio
async def test_ride_emergency_cannot_overwrite_existing_open_alert() -> None:
    first_requested_at = datetime(2026, 9, 16, 10, 0, tzinfo=UTC)
    ride = Ride(
        id=RIDE_ID,
        passenger_user_id=USER_ID,
        emergency_status="open",
        emergency_requested_at=first_requested_at,
        emergency_note="Premiere alerte",
        pickup_location=GeoPoint(lat=5.35, lng=-4.0),
        dropoff_location=GeoPoint(lat=5.36, lng=-3.99),
        requested_at=datetime.now(UTC),
    )
    repo = FakeRideRepo(ride)
    service = RideService(
        ride_repo=repo,
        routing=FakeRouting(),
        pricing_rules=FakePricingRules(),
        emergency_contact_repo=FakeEmergencyContactRepo(),
        emergency_notifications=FakeNotifier(),
    )

    with pytest.raises(ApiError) as exc_info:
        await service.request_emergency(
            RIDE_ID,
            actor_user_id=USER_ID,
            actor_role="user",
            note="Deuxieme alerte",
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "EMERGENCY_ALREADY_OPEN"
    assert repo.saved is False
    assert ride.emergency_requested_at == first_requested_at
    assert ride.emergency_note == "Premiere alerte"
