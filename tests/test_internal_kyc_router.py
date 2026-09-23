from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import FastAPI

from app_base.core.auth_deps import require_s2s_admin_actor
from app_base.core.deps import backoffice_audit_repo, driver_service, kyc_command_store, session_dep
from app_base.core.errors import ApiError, api_error_handler
from app_base.core.s2s_command_store import S2SCommandStore
from app_base.core.service_scopes import KYC_DECIDE, KYC_READ
from app_base.modules.audit.domain.entities import BackofficeAuditEvent
from app_base.modules.auth.domain.entities import User, UserRole, UserStatus
from app_base.modules.ride.presentation.kyc_internal_router import router

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


class FakeDriverService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, UUID, UUID, str | None]] = []

    async def list_kyc_queue(self, *, status: str, page: int, page_size: int) -> dict:
        return {"status": status, "page": page, "page_size": page_size}

    async def get_kyc_detail(self, driver_id: UUID) -> dict:
        return {"driver_id": str(driver_id)}

    async def approve_kyc(self, driver_id: UUID, *, reviewed_by_user_id: UUID, notes: str | None) -> dict:
        self.calls.append(("approve", driver_id, reviewed_by_user_id, notes))
        return {"id": str(driver_id), "status": "active"}

    async def reject_kyc(self, driver_id: UUID, *, reviewed_by_user_id: UUID, notes: str | None) -> dict:
        self.calls.append(("reject", driver_id, reviewed_by_user_id, notes))
        return {"id": str(driver_id), "status": "suspended"}


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def find_by_id(self, user_id: UUID) -> User | None:
        if self.user is not None and self.user.id == user_id:
            return self.user
        return None


@pytest.fixture
def kyc_api(monkeypatch):
    scopes: list[set[str]] = []
    service = FakeDriverService()
    commands = S2SCommandStore(FakeRedis(), namespace="kyc-command")  # type: ignore[arg-type]
    audit = FakeAuditRepository()
    session = FakeSession()
    actor = User(id=uuid4(), phone="+2250700000000", role=UserRole.ADMIN, status=UserStatus.ACTIVE)

    def decode(token, *, audience, required_scopes, client_id, expected_subject=None):
        assert token == "service-token"
        assert audience == "diddigo"
        assert client_id == "backoffice-staging-diddigo"
        assert expected_subject == "service:backoffice"
        scopes.append(required_scopes)
        return {"sub": "service:backoffice", "client_id": client_id}

    monkeypatch.setattr("app_base.core.auth_deps.decode_identity_service_token", decode)
    app = FastAPI()
    app.add_exception_handler(ApiError, api_error_handler)
    app.include_router(router)
    app.dependency_overrides[driver_service] = lambda: service
    app.dependency_overrides[require_s2s_admin_actor] = lambda: actor
    app.dependency_overrides[kyc_command_store] = lambda: commands
    app.dependency_overrides[backoffice_audit_repo] = lambda: audit
    app.dependency_overrides[session_dep] = lambda: session
    app.state.audit = audit
    app.state.fake_session = session
    return app, service, actor, scopes


def _headers(*, actor_id: UUID | None = None, idempotency_key: str | None = None) -> dict[str, str]:
    headers = {
        "Authorization": "Bearer service-token",
        "X-Client-ID": "backoffice-staging-diddigo",
        "X-Request-ID": str(uuid4()),
    }
    if actor_id:
        headers["X-User-ID"] = str(actor_id)
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


async def test_s2s_actor_must_be_an_active_local_admin() -> None:
    actor_id = uuid4()
    passenger = User(
        id=actor_id,
        phone="+2250700000001",
        role=UserRole.PASSENGER,
        status=UserStatus.ACTIVE,
    )
    with pytest.raises(ApiError) as forbidden:
        await require_s2s_admin_actor(
            backoffice_actor_id=None,
            actor_user_id=actor_id,
            repo=FakeUserRepository(passenger),  # type: ignore[arg-type]
        )
    assert forbidden.value.status_code == 403
    assert forbidden.value.code == "SERVICE_ACTOR_FORBIDDEN"

    admin = User(
        id=actor_id,
        phone="+2250700000002",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    assert await require_s2s_admin_actor(
        backoffice_actor_id=None,
        actor_user_id=actor_id,
        repo=FakeUserRepository(admin),  # type: ignore[arg-type]
    ) == admin


async def test_s2s_actor_accepts_canonical_header_and_rejects_header_mismatch() -> None:
    actor_id = uuid4()
    admin = User(
        id=actor_id,
        phone="+2250700000002",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    repo = FakeUserRepository(admin)

    assert await require_s2s_admin_actor(
        backoffice_actor_id=actor_id,
        actor_user_id=None,
        repo=repo,  # type: ignore[arg-type]
    ) == admin

    with pytest.raises(ApiError) as mismatch:
        await require_s2s_admin_actor(
            backoffice_actor_id=actor_id,
            actor_user_id=uuid4(),
            repo=repo,  # type: ignore[arg-type]
        )
    assert mismatch.value.status_code == 400
    assert mismatch.value.code == "SERVICE_ACTOR_HEADER_MISMATCH"


async def test_s2s_actor_requires_one_actor_header() -> None:
    with pytest.raises(ApiError) as missing:
        await require_s2s_admin_actor(
            backoffice_actor_id=None,
            actor_user_id=None,
            repo=FakeUserRepository(None),  # type: ignore[arg-type]
        )
    assert missing.value.status_code == 422
    assert missing.value.code == "SERVICE_ACTOR_REQUIRED"


async def test_s2s_kyc_reads_require_read_scope(kyc_api) -> None:
    app, _, _, scopes = kyc_api
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/internal/v1/drivers/kyc", headers=_headers())
    assert response.status_code == 200
    assert scopes == [{KYC_READ}]


async def test_s2s_kyc_decision_requires_idempotency_key(kyc_api) -> None:
    app, _, actor, _ = kyc_api
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/internal/v1/drivers/{uuid4()}/kyc/approve",
            headers=_headers(actor_id=actor.id),
            json={"notes": "conforme"},
        )
    assert response.status_code == 422


async def test_s2s_kyc_decision_requires_request_id(kyc_api) -> None:
    app, _, actor, _ = kyc_api
    headers = _headers(actor_id=actor.id, idempotency_key="kyc-decision-000")
    headers.pop("X-Request-ID")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/internal/v1/drivers/{uuid4()}/kyc/approve",
            headers=headers,
            json={"notes": "conforme"},
        )
    assert response.status_code == 422


async def test_s2s_kyc_decision_is_replayed_once_and_uses_decide_scope(kyc_api) -> None:
    app, service, actor, scopes = kyc_api
    driver_id = uuid4()
    headers = _headers(actor_id=actor.id, idempotency_key="kyc-decision-001")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post(
            f"/internal/v1/drivers/{driver_id}/kyc/approve", headers=headers, json={"notes": "conforme"},
        )
        replay = await client.post(
            f"/internal/v1/drivers/{driver_id}/kyc/approve", headers=headers, json={"notes": "conforme"},
        )

    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    assert service.calls == [("approve", driver_id, actor.id, "conforme")]
    assert scopes[-1] == {KYC_DECIDE}
    assert app.state.fake_session.commits == 1
    assert len(app.state.audit.events) == 1
    event = app.state.audit.events[0]
    assert event.action == "driver.kyc.approve"
    assert event.target_id == driver_id
    assert event.actor_user_id == actor.id
    assert event.reason == "conforme"


async def test_s2s_kyc_rejects_divergent_reuse(kyc_api) -> None:
    app, _, actor, _ = kyc_api
    driver_id = uuid4()
    headers = _headers(actor_id=actor.id, idempotency_key="kyc-decision-002")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/internal/v1/drivers/{driver_id}/kyc/reject", headers=headers, json={"notes": "illisible"},
        )
        conflict = await client.post(
            f"/internal/v1/drivers/{driver_id}/kyc/reject", headers=headers, json={"notes": "expire"},
        )
    assert response.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
