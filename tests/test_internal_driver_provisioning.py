from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI

from app_base.core.auth_deps import require_s2s_admin_actor
from app_base.core.deps import (
    backoffice_audit_repo,
    driver_provisioning_command_store,
    driver_provisioning_service,
    session_dep,
)
from app_base.core.errors import ApiError, api_error_handler
from app_base.core.s2s_command_store import S2SCommandStore
from app_base.core.service_scopes import DRIVERS_WRITE
from app_base.modules.audit.domain.entities import BackofficeAuditEvent
from app_base.modules.auth.domain.entities import User, UserRole, UserStatus
from app_base.modules.ride.application.driver_provisioning_service import DriverProvisioningService
from app_base.modules.ride.presentation.driver_internal_router import router

pytestmark = pytest.mark.unit


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def set(self, key: str, value: str, *, ex: int, nx: bool = False):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def get(self, key: str):
        return self.values.get(key)

    async def delete(self, key: str):
        self.values.pop(key, None)


class FakeAuditRepository:
    def __init__(self) -> None:
        self.events: list[BackofficeAuditEvent] = []

    async def record(self, event: BackofficeAuditEvent) -> BackofficeAuditEvent:
        self.events.append(event)
        return event


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class FakeUsers:
    def __init__(self) -> None:
        self.items: dict[UUID, User] = {}
        self.commits = 0

    async def find_by_id(self, user_id: UUID) -> User | None:
        return self.items.get(user_id)

    async def save(self, user: User) -> User:
        self.items[user.id] = user
        return user

    async def commit(self) -> None:
        self.commits += 1


class FakeDriverRepo:
    def __init__(self) -> None:
        self.user_ids: set[UUID] = set()

    async def find_by_user_id(self, user_id: UUID):
        return object() if user_id in self.user_ids else None


class FakeDrivers:
    def __init__(self) -> None:
        self.driver_repo = FakeDriverRepo()
        self.profiles: dict[UUID, dict] = {}
        self.create_calls = 0

    async def create_profile(self, *, user_id: UUID, **fields) -> dict:
        self.create_calls += 1
        profile = _profile(user_id, fields)
        self.profiles[user_id] = profile
        self.driver_repo.user_ids.add(user_id)
        return profile

    async def get_profile(self, user_id: UUID) -> dict:
        return self.profiles[user_id]


def _fields(license_number: str = "CI-123456") -> dict:
    return {
        "license_number": license_number,
        "legal_name": "Awa Kone",
        "birth_date": None,
        "residence_address": None,
        "license_document_file_id": None,
        "license_back_document_file_id": None,
        "national_id_document_file_id": None,
        "national_id_back_document_file_id": None,
        "selfie_document_file_id": None,
        "license_document_url": None,
        "license_back_document_url": None,
        "national_id_document_url": None,
        "national_id_back_document_url": None,
        "selfie_document_url": None,
    }


def _profile(user_id: UUID, fields: dict) -> dict:
    return {
        "id": str(uuid4()),
        "user_id": str(user_id),
        "license_number": fields["license_number"],
        "status": "pending_verification",
        "kyc": {key: value for key, value in fields.items() if key != "license_number"}
        | {"submitted_at": "2026-09-22T00:00:00Z", "reviewed_at": None, "review_notes": None},
    }


async def test_provision_creates_shadow_and_pending_driver_profile() -> None:
    users = FakeUsers()
    drivers = FakeDrivers()
    service = DriverProvisioningService(users=users, drivers=drivers)  # type: ignore[arg-type]
    user_id = uuid4()

    result = await service.provision(user_id=user_id, full_name="Awa Kone", profile_fields=_fields())

    assert result["created"] is True
    assert result["profile"]["status"] == "pending_verification"
    assert users.items[user_id].role == UserRole.PASSENGER
    assert users.items[user_id].phone.startswith("+000")
    assert users.commits == 0


async def test_provision_is_idempotent_and_rejects_divergent_profile() -> None:
    users = FakeUsers()
    drivers = FakeDrivers()
    service = DriverProvisioningService(users=users, drivers=drivers)  # type: ignore[arg-type]
    user_id = uuid4()

    await service.provision(user_id=user_id, full_name=None, profile_fields=_fields())
    replay = await service.provision(user_id=user_id, full_name=None, profile_fields=_fields())
    assert replay["created"] is False
    assert drivers.create_calls == 1

    with pytest.raises(ApiError) as conflict:
        await service.provision(user_id=user_id, full_name=None, profile_fields=_fields("CI-OTHER"))
    assert conflict.value.status_code == 409
    assert conflict.value.code == "DRIVER_PROVISIONING_CONFLICT"


async def test_internal_provision_route_requires_scope_and_replays_command(monkeypatch) -> None:
    scopes: list[set[str]] = []
    calls = 0
    target_user_id = uuid4()
    actor = User(id=uuid4(), phone="+2250700000099", role=UserRole.ADMIN, status=UserStatus.ACTIVE)

    def decode(token, *, audience, required_scopes, client_id, expected_subject=None):
        assert token == "service-token"
        assert audience == "diddigo"
        assert client_id == "backoffice-staging-diddigo"
        assert expected_subject == "service:backoffice"
        scopes.append(required_scopes)
        return {"sub": "service:backoffice", "client_id": client_id}

    class Provisioner:
        async def provision(self, **kwargs):
            nonlocal calls
            calls += 1
            return {"created": True, "profile": {"id": str(uuid4()), "user_id": str(kwargs["user_id"])}}

    monkeypatch.setattr("app_base.core.auth_deps.decode_identity_service_token", decode)
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    app.include_router(router)
    app.dependency_overrides[require_s2s_admin_actor] = lambda: actor
    app.dependency_overrides[driver_provisioning_service] = lambda: Provisioner()
    commands = S2SCommandStore(FakeRedis(), namespace="driver-provision")  # type: ignore[arg-type]
    audit = FakeAuditRepository()
    session = FakeSession()
    app.dependency_overrides[driver_provisioning_command_store] = lambda: commands
    app.dependency_overrides[backoffice_audit_repo] = lambda: audit
    app.dependency_overrides[session_dep] = lambda: session
    headers = {
        "Authorization": "Bearer service-token",
        "X-Client-ID": "backoffice-staging-diddigo",
        "X-User-ID": str(actor.id),
        "X-Request-ID": str(uuid4()),
        "Idempotency-Key": "driver-provision-001",
    }
    body = {"user_id": str(target_user_id), "license_number": "CI-123456"}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post("/internal/v1/drivers/provision", headers=headers, json=body)
        replay = await client.post("/internal/v1/drivers/provision", headers=headers, json=body)

    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert calls == 1
    assert scopes == [{DRIVERS_WRITE}, {DRIVERS_WRITE}]
    assert session.commits == 1
    assert len(audit.events) == 1
    assert audit.events[0].action == "driver.profile.provision"
    assert audit.events[0].target_id == target_user_id
    assert audit.events[0].actor_user_id == actor.id
    assert audit.events[0].client_id == "backoffice-staging-diddigo"
