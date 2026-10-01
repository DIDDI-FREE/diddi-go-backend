from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from app_base.core.auth_deps import require_s2s_admin_actor
from app_base.core.deps import (
    backoffice_audit_repo,
    partner_command_store,
    partner_service,
    session_dep,
)
from app_base.core.errors import ApiError, api_error_handler
from app_base.core.service_scopes import PARTNERS_READ, PARTNERS_WRITE
from app_base.modules.auth.domain.entities import User, UserRole, UserStatus
from app_base.modules.partner.presentation.internal_router import router

pytestmark = pytest.mark.unit


class FakePartnerService:
    def __init__(self) -> None:
        self.suspended: list = []

    async def list_partners(self, *, status, partner_type, page, page_size) -> dict:
        return {"items": [], "page": page, "page_size": page_size}

    async def suspend_partner(self, partner_id) -> dict:
        self.suspended.append(partner_id)
        return {"id": str(partner_id), "status": "suspended"}


class FakeAudit:
    def __init__(self) -> None:
        self.events: list = []

    async def record(self, event):
        self.events.append(event)
        return event


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class FakeCommandStore:
    def __init__(self) -> None:
        self.completed: list = []
        self.released = 0

    async def reserve(self, *, client_id, idempotency_key, payload):
        return SimpleNamespace(cached_response=None, key=idempotency_key)

    async def complete(self, reservation, response) -> None:
        self.completed.append(response)

    async def release(self, reservation) -> None:
        self.released += 1


def _build(monkeypatch):
    scopes: list[set[str]] = []
    service = FakePartnerService()
    audit = FakeAudit()
    session = FakeSession()
    commands = FakeCommandStore()
    actor = User(id=uuid4(), phone="+2250700000900", role=UserRole.ADMIN, status=UserStatus.ACTIVE)

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
    app.dependency_overrides[partner_service] = lambda: service
    app.dependency_overrides[require_s2s_admin_actor] = lambda: actor
    app.dependency_overrides[partner_command_store] = lambda: commands
    app.dependency_overrides[backoffice_audit_repo] = lambda: audit
    app.dependency_overrides[session_dep] = lambda: session
    return app, service, audit, session, commands, actor, scopes


def _headers(*, idempotency: bool = True) -> dict[str, str]:
    headers = {
        "Authorization": "Bearer service-token",
        "X-Client-ID": "backoffice-staging-diddigo",
        "X-Request-ID": str(uuid4()),
    }
    if idempotency:
        headers["Idempotency-Key"] = "partner-cmd-00000001"
    return headers


@pytest.mark.asyncio
async def test_s2s_list_requires_partners_read_scope(monkeypatch) -> None:
    app, _service, _audit, _session, _commands, _actor, scopes = _build(monkeypatch)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/internal/v1/admin/partners", headers=_headers(idempotency=False))
    assert resp.status_code == 200
    assert scopes == [{PARTNERS_READ}]


@pytest.mark.asyncio
async def test_s2s_write_authorizes_runs_and_audits(monkeypatch) -> None:
    app, service, audit, session, commands, actor, scopes = _build(monkeypatch)
    partner_id = uuid4()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(f"/internal/v1/admin/partners/{partner_id}/suspend", headers=_headers())
    assert resp.status_code == 200
    assert resp.json()["status"] == "suspended"
    assert scopes == [{PARTNERS_WRITE}]           # write scope enforced
    assert service.suspended == [partner_id]       # service op ran
    assert session.commits == 1                    # committed in-txn
    assert len(audit.events) == 1                  # durable audit recorded
    event = audit.events[0]
    assert event.action == "partner.suspend"
    assert event.target_id == partner_id
    assert event.actor_user_id == actor.id
    assert commands.completed and not commands.released  # idempotency completed, not released


@pytest.mark.asyncio
async def test_s2s_write_requires_idempotency_key(monkeypatch) -> None:
    app, *_ = _build(monkeypatch)
    partner_id = uuid4()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/internal/v1/admin/partners/{partner_id}/suspend", headers=_headers(idempotency=False),
        )
    assert resp.status_code == 422  # missing Idempotency-Key header
