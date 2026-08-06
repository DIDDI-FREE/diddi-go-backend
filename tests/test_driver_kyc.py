from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from app_base.modules.ride.application.driver_service import DriverService

pytestmark = pytest.mark.unit


class FakeDriverRepo:
    def __init__(self) -> None:
        self.profile = None

    async def find_by_user_id(self, user_id):
        if self.profile and self.profile.user_id == user_id:
            return self.profile
        return None

    async def find_by_id(self, profile_id):
        if self.profile and self.profile.id == profile_id:
            return self.profile
        return None

    async def save(self, profile):
        self.profile = profile
        return profile


class FakeVehicleRepo:
    def __init__(self) -> None:
        self.vehicle = None

    async def save(self, vehicle):
        self.vehicle = vehicle
        return vehicle

    async def find_active_for_driver(self, driver_id):
        return None


@pytest.mark.asyncio
async def test_create_driver_profile_stores_kyc_fields() -> None:
    repo = FakeDriverRepo()
    service = DriverService(driver_repo=repo, vehicle_repo=FakeVehicleRepo())
    user_id = uuid4()
    license_file_id = uuid4()
    national_id_file_id = uuid4()
    selfie_file_id = uuid4()

    payload = await service.create_profile(
        user_id=user_id,
        license_number=" CI-123456 ",
        legal_name=" Awa Kone ",
        birth_date=date(1992, 4, 20),
        residence_address=" Cocody, Abidjan ",
        license_document_file_id=license_file_id,
        national_id_document_file_id=national_id_file_id,
        selfie_document_file_id=selfie_file_id,
        license_document_url=" https://cdn.example/license.jpg ",
        national_id_document_url="https://cdn.example/id.jpg",
        selfie_document_url="https://cdn.example/selfie.jpg",
    )

    assert payload["license_number"] == "CI-123456"
    assert payload["status"] == "pending_verification"
    assert payload["kyc"]["legal_name"] == "Awa Kone"
    assert payload["kyc"]["birth_date"] == "1992-04-20"
    assert payload["kyc"]["residence_address"] == "Cocody, Abidjan"
    assert payload["kyc"]["license_document_file_id"] == str(license_file_id)
    assert payload["kyc"]["national_id_document_file_id"] == str(national_id_file_id)
    assert payload["kyc"]["selfie_document_file_id"] == str(selfie_file_id)
    assert payload["kyc"]["license_document_url"] == "https://cdn.example/license.jpg"
    assert payload["kyc"]["national_id_document_url"] == "https://cdn.example/id.jpg"
    assert payload["kyc"]["selfie_document_url"] == "https://cdn.example/selfie.jpg"
    assert payload["kyc"]["submitted_at"] is not None
    assert repo.profile.user_id == user_id
    assert repo.profile.license_verified_at is None
    assert repo.profile.license_document_file_id == license_file_id


@pytest.mark.asyncio
async def test_admin_approval_activates_driver_profile() -> None:
    repo = FakeDriverRepo()
    service = DriverService(driver_repo=repo, vehicle_repo=FakeVehicleRepo())
    user_id = uuid4()
    admin_id = uuid4()

    created = await service.create_profile(user_id=user_id, license_number="CI-123456")
    approved = await service.approve_kyc(
        driver_id=UUID(created["id"]),
        reviewed_by_user_id=admin_id,
        notes="Documents OK",
    )

    assert approved["status"] == "active"
    assert approved["kyc"]["reviewed_at"] is not None
    assert repo.profile.license_verified_at is not None


@pytest.mark.asyncio
async def test_register_vehicle_stores_registration_file_id() -> None:
    driver_repo = FakeDriverRepo()
    vehicle_repo = FakeVehicleRepo()
    service = DriverService(driver_repo=driver_repo, vehicle_repo=vehicle_repo)
    user_id = uuid4()
    registration_file_id = uuid4()

    await service.create_profile(user_id=user_id, license_number="CI-123456")
    payload = await service.register_vehicle(
        user_id=user_id,
        plate_number=" ce-123-aa ",
        make="Toyota",
        model="Yaris",
        color="gris",
        category="standard",
        registration_document_file_id=registration_file_id,
    )

    assert payload["plate_number"] == "CE-123-AA"
    assert payload["registration_document_file_id"] == str(registration_file_id)
    assert vehicle_repo.vehicle.registration_document_file_id == registration_file_id
