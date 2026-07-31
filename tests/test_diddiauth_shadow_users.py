from types import SimpleNamespace
from uuid import uuid4

import pytest

from app_base.core.auth_deps import _upsert_identity_shadow_user, require_business_driver
from app_base.core.errors import ApiError
from app_base.modules.auth.domain.entities import UserRole, UserStatus
from app_base.modules.ride.domain.entities import DriverProfile, DriverStatus

pytestmark = pytest.mark.unit


class FakeUserRepo:
    def __init__(self) -> None:
        self.saved = None
        self.committed = False

    async def save(self, user):
        self.saved = user
        return user

    async def commit(self) -> None:
        self.committed = True


class FakeDriverRepo:
    def __init__(self, profile):
        self.profile = profile

    async def find_by_user_id(self, user_id):
        if self.profile and self.profile.user_id == user_id:
            return self.profile
        return None


@pytest.mark.asyncio
async def test_diddiauth_user_is_shadowed_as_local_passenger():
    user_id = uuid4()
    repo = FakeUserRepo()
    identity_user = SimpleNamespace(
        id=user_id,
        phone="+237699000000",
        full_name="Diddi User",
        role="passenger",
        status="active",
        created_at=None,
        updated_at=None,
    )

    await _upsert_identity_shadow_user(identity_user, repo)

    assert repo.saved.id == user_id
    assert repo.saved.phone == "+237699000000"
    assert repo.saved.role is UserRole.PASSENGER
    assert repo.saved.status is UserStatus.ACTIVE
    assert repo.committed is True


@pytest.mark.asyncio
async def test_diddiauth_admin_is_shadowed_as_local_admin():
    repo = FakeUserRepo()
    identity_user = SimpleNamespace(
        id=uuid4(),
        phone="",
        full_name="Admin",
        role="admin",
        status="active",
        created_at=None,
        updated_at=None,
    )

    await _upsert_identity_shadow_user(identity_user, repo)

    assert repo.saved.role is UserRole.ADMIN
    assert repo.saved.phone.startswith("+000")


@pytest.mark.asyncio
async def test_business_driver_requires_active_local_driver_profile():
    user_id = uuid4()
    profile = DriverProfile(
        id=uuid4(),
        user_id=user_id,
        license_number="DL-001",
        status=DriverStatus.ACTIVE,
    )
    user = SimpleNamespace(id=user_id, role="passenger", status="active")

    resolved = await require_business_driver(user=user, driver_repo=FakeDriverRepo(profile))

    assert resolved == profile


@pytest.mark.asyncio
async def test_business_driver_rejects_user_without_driver_profile():
    user = SimpleNamespace(id=uuid4(), role="passenger", status="active")

    with pytest.raises(ApiError) as excinfo:
        await require_business_driver(user=user, driver_repo=FakeDriverRepo(None))

    assert excinfo.value.code == "DRIVER_PROFILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_admin_bypasses_business_driver_gate():
    user = SimpleNamespace(id=uuid4(), role="admin", status="active")

    resolved = await require_business_driver(user=user, driver_repo=FakeDriverRepo(None))

    assert resolved is None
