from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.partner.application.services import PartnerService
from app_base.modules.partner.domain.entities import (
    Partner,
    PartnerDriverLink,
    PartnerMember,
    PartnerStatus,
    PartnerType,
    VehicleAssignment,
)
from app_base.modules.ride.application.matching_service import MatchingService
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    DriverProfile,
    DriverStatus,
    Ride,
    Vehicle,
    VehicleCategory,
)

pytestmark = pytest.mark.unit


class FakePartnerRepo:
    def __init__(self) -> None:
        self.partners: dict = {}
        self.members: dict = {}
        self.driver_links: dict = {}
        self.assignments: dict = {}
        self.vehicle_owners: dict = {}

    async def save(self, partner: Partner) -> Partner:
        self.partners[partner.id] = partner
        return partner

    async def find_by_id(self, partner_id):
        return self.partners.get(partner_id)

    async def list_by(self, *, status=None, partner_type=None, page=1, page_size=20):
        partners = list(self.partners.values())
        if status is not None:
            partners = [partner for partner in partners if partner.status == status]
        if partner_type is not None:
            partners = [partner for partner in partners if partner.partner_type == partner_type]
        return partners[(page - 1) * page_size : page * page_size], len(partners)

    async def save_member(self, member: PartnerMember) -> PartnerMember:
        self.members[member.id] = member
        return member

    async def list_members(self, partner_id):
        return [member for member in self.members.values() if member.partner_id == partner_id]

    async def find_active_memberships_by_user_id(self, user_id):
        return [
            (self.partners[member.partner_id], member)
            for member in self.members.values()
            if member.user_id == user_id and member.active
        ]

    async def deactivate_member(self, member_id):
        member = self.members.get(member_id)
        if member is None:
            return False
        member.active = False
        return True

    async def save_driver_link(self, link: PartnerDriverLink) -> PartnerDriverLink:
        self.driver_links[link.id] = link
        return link

    async def find_active_driver_link(self, driver_id):
        for link in self.driver_links.values():
            if link.driver_id == driver_id and link.active:
                return self.partners[link.partner_id], link
        return None

    async def list_driver_links(self, partner_id, *, active_only=True):
        return [
            link
            for link in self.driver_links.values()
            if link.partner_id == partner_id and (not active_only or link.active)
        ]

    async def end_driver_link(self, partner_id, driver_id):
        for link in self.driver_links.values():
            if link.partner_id == partner_id and link.driver_id == driver_id and link.active:
                link.active = False
                return True
        return False

    async def set_vehicle_partner_owner(self, vehicle_id, partner_id, driver_id):
        self.vehicle_owners[vehicle_id] = (partner_id, driver_id)
        return True

    async def save_vehicle_assignment(self, assignment: VehicleAssignment) -> VehicleAssignment:
        self.assignments[assignment.id] = assignment
        return assignment

    async def find_active_vehicle_assignment(self, vehicle_id):
        for assignment in self.assignments.values():
            if assignment.vehicle_id == vehicle_id and assignment.active:
                return assignment
        return None

    async def end_vehicle_assignment(self, vehicle_id):
        for assignment in self.assignments.values():
            if assignment.vehicle_id == vehicle_id and assignment.active:
                assignment.active = False
                return True
        return False


class FakeDriverRepo:
    def __init__(self, profile: DriverProfile) -> None:
        self.profile = profile

    async def find_by_user_id(self, user_id):
        return self.profile if self.profile.user_id == user_id else None


class FakeVehicleRepo:
    def __init__(self, vehicle: Vehicle) -> None:
        self.vehicle = vehicle

    async def find_active_for_driver(self, driver_id):
        return self.vehicle if self.vehicle.driver_id == driver_id and self.vehicle.active else None


@pytest.mark.asyncio
async def test_partner_commission_percentage_is_validated() -> None:
    service = PartnerService(partner_repo=FakePartnerRepo())

    with pytest.raises(ApiError) as exc_info:
        await service.create_partner(
            name="Fleet",
            partner_type="fleet_owner",
            partner_commission_enabled=True,
            partner_commission_mode="percentage",
            partner_commission_rate=Decimal("1.20"),
        )

    assert exc_info.value.code == "INVALID_PARTNER_COMMISSION"


@pytest.mark.asyncio
async def test_partner_activation_and_driver_affiliation() -> None:
    repo = FakePartnerRepo()
    service = PartnerService(partner_repo=repo)
    partner = await service.create_partner(name="Fleet", partner_type="fleet_owner")
    partner_id = UUID(partner["id"])

    await service.activate_partner(partner_id)
    link = await service.affiliate_driver(partner_id, driver_id=uuid4())

    assert link["partner_id"] == str(partner_id)
    assert link["active"] is True


@pytest.mark.asyncio
async def test_matching_rejects_driver_when_active_partner_is_suspended() -> None:
    driver_user_id = uuid4()
    driver_id = uuid4()
    repo = FakePartnerRepo()
    partner_service = PartnerService(partner_repo=repo)
    partner = Partner(
        id=uuid4(),
        name="Fleet",
        partner_type=PartnerType.FLEET_OWNER,
        status=PartnerStatus.SUSPENDED,
    )
    await repo.save(partner)
    await repo.save_driver_link(PartnerDriverLink(id=uuid4(), partner_id=partner.id, driver_id=driver_id))
    service = MatchingService(
        ride_repo=None,
        driver_repo=FakeDriverRepo(
            DriverProfile(id=driver_id, user_id=driver_user_id, license_number="CI-123", status=DriverStatus.ACTIVE)
        ),
        vehicle_repo=FakeVehicleRepo(
            Vehicle(
                id=uuid4(),
                driver_id=driver_id,
                plate_number="CI-123-AA",
                category=VehicleCategory.STANDARD,
                comfort_level=ComfortLevel.STANDARD,
            )
        ),
        locations=None,
        offers=None,
        partner_service=partner_service,
    )
    ride = Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.STANDARD,
    )

    can_take, reason = await service._can_take_ride(driver_user_id, ride)

    assert can_take is False
    assert reason == "partner_not_active:suspended"
