"""Ticket 084: DiddiGo tells DiddiFreeID when a driver is enabled, suspended or rejected."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
import pytest

from app_base.modules.ride.application import driver_access_sync
from app_base.modules.ride.application.driver_access_sync import (
    DriverAccessStatusDispatcher,
    DriverAccessStatusPublisher,
)
from app_base.modules.ride.application.driver_service import KYC_DOCUMENT_TYPES, DriverService
from app_base.modules.ride.domain.driver_access import first_approval_from_history
from app_base.modules.ride.infra.identity_capability_client import (
    CapabilityDeliveryError,
    IdentityCapabilityClient,
)
from tests.test_driver_kyc import FakeDriverRepo, FakeVehicleRepo, full_kyc_documents

DOCS = set(KYC_DOCUMENT_TYPES)
REJECTION = [{
    "document_type": "license_front", "decision": "rejected", "reason_code": "unreadable",
    "reason": "Photo illisible.", "expected_correction": "Renvoyer une photo nette.",
}]


class MemoryAccessRepo:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def last_status(self, user_id):
        mine = [event for event in self.events if event["user_id"] == user_id]
        return mine[-1]["access_status"] if mine else None

    async def enqueue(self, **kwargs):
        self.events.append(kwargs)
        return kwargs


def _service():
    access = MemoryAccessRepo()
    service = DriverService(
        driver_repo=FakeDriverRepo(),
        vehicle_repo=FakeVehicleRepo(),
        access_publisher=DriverAccessStatusPublisher(access, required_documents=DOCS),
    )
    return service, access


def _statuses(access: MemoryAccessRepo) -> list[tuple[str, str]]:
    return [(event["access_status"], event["reason"]) for event in access.events]


# --- what is sent, and when -----------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_approval_enables_rejection_of_an_active_driver_suspends_reapproval_enables() -> None:
    service, access = _service()
    created = await service.create_profile(user_id=uuid4(), license_number="CI-1", **full_kyc_documents())
    driver_id = UUID(created["id"])

    await service.approve_kyc(driver_id=driver_id, reviewed_by_user_id=uuid4())
    await service.reject_kyc(driver_id=driver_id, reviewed_by_user_id=uuid4(), documents=REJECTION)
    await service.approve_kyc(driver_id=driver_id, reviewed_by_user_id=uuid4())

    assert _statuses(access) == [
        ("enabled", "kyc_approved"), ("suspended", "kyc_rejected"), ("enabled", "kyc_approved"),
    ]
    assert all(event["source"] == "kyc" and event.get("enabled_at") is None for event in access.events)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_rejection_before_any_approval_is_rejected_and_waiting_sends_nothing() -> None:
    service, access = _service()
    created = await service.create_profile(user_id=uuid4(), license_number="CI-1", **full_kyc_documents())
    assert access.events == []  # submitted, waiting: DiddiFreeID keeps `requested`

    await service.reject_kyc(driver_id=UUID(created["id"]), reviewed_by_user_id=uuid4(), documents=REJECTION)

    assert _statuses(access) == [("rejected", "kyc_rejected")]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_active_driver_who_resubmits_documents_is_suspended_until_reviewed() -> None:
    service, access = _service()
    user_id = uuid4()
    created = await service.create_profile(user_id=user_id, license_number="CI-1", **full_kyc_documents())
    await service.approve_kyc(driver_id=UUID(created["id"]), reviewed_by_user_id=uuid4())

    await service.resubmit_kyc(user_id=user_id, license_document_file_id=uuid4())

    assert _statuses(access) == [("enabled", "kyc_approved"), ("suspended", "kyc_resubmitted")]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_same_status_is_never_queued_twice() -> None:
    service, access = _service()
    created = await service.create_profile(user_id=uuid4(), license_number="CI-1", **full_kyc_documents())
    driver_id = UUID(created["id"])
    await service.approve_kyc(driver_id=driver_id, reviewed_by_user_id=uuid4())
    await service.approve_kyc(driver_id=driver_id, reviewed_by_user_id=uuid4())
    assert _statuses(access) == [("enabled", "kyc_approved")]


@pytest.mark.unit
def test_first_approval_survives_later_rejections_and_resubmissions() -> None:
    def entries(when: str, status: str) -> list[dict]:
        return [{"document_type": doc, "status": status, "reviewed_at": when} for doc in DOCS]

    history = (
        entries("2026-01-10T09:00:00+00:00", "rejected")
        + entries("2026-02-01T10:00:00+00:00", "approved")
        + entries("2026-06-01T10:00:00+00:00", "rejected")
        + entries("2026-06-05T10:00:00+00:00", "approved")
    )
    assert first_approval_from_history(history, required_documents=DOCS) == datetime(2026, 2, 1, 10, tzinfo=UTC)
    # One document never approved: no approval date.
    partial = [entry for entry in history if entry["document_type"] != "selfie"]
    assert first_approval_from_history(partial, required_documents=DOCS) is None


# --- sending ----------------------------------------------------------------------------------------


class FakeClient:
    def __init__(self, error: CapabilityDeliveryError | None = None) -> None:
        self.error = error
        self.sent: list = []

    async def send_driver_access_status(self, event):
        self.sent.append(event)
        if self.error is not None:
            raise self.error


class FakeEvent:
    def __init__(self, user_id, created_at: int, access_status: str = "enabled") -> None:
        self.user_id = user_id
        self.created_at = created_at
        self.access_status = access_status
        self.event_id = f"e-{uuid4()}"
        self.source = "kyc"
        self.attempts = 0
        self.status = "pending"


class FakeQueue:
    def __init__(self, events) -> None:
        self.events = events

    async def list_due(self, *, now, limit):
        return [event for event in self.events if event.status in {"pending", "retry"}][:limit]

    async def has_waiting_before(self, event):
        return any(
            other.user_id == event.user_id and other.created_at < event.created_at
            and other.status in {"pending", "retry"}
            for other in self.events
        )

    async def mark_delivered(self, event, *, now):
        event.status = "delivered"

    async def mark_retry(self, event, *, next_attempt_at, error):
        event.status, event.attempts = "retry", event.attempts + 1

    async def mark_refused(self, event, *, error):
        event.status = "refused"


@pytest.fixture
def sync_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(driver_access_sync.settings, "driver_access_status_sync_enabled", True)


@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "final"),
    [
        (None, "delivered"),
        (CapabilityDeliveryError("down", status_code=503), "retry"),
        (CapabilityDeliveryError("timeout"), "retry"),
        (CapabilityDeliveryError("scope", status_code=403), "retry"),
        (CapabilityDeliveryError("bad", status_code=422), "refused"),
        (CapabilityDeliveryError("no user", status_code=404), "refused"),
    ],
)
async def test_delivery_outcomes(sync_on, error, final) -> None:
    event = FakeEvent(uuid4(), 1)
    await DriverAccessStatusDispatcher(FakeQueue([event]), FakeClient(error)).deliver_due(batch_size=10)
    assert event.status == final


@pytest.mark.unit
@pytest.mark.asyncio
async def test_statuses_of_one_driver_are_sent_in_order(sync_on) -> None:
    user = uuid4()
    first, second = FakeEvent(user, 1, "enabled"), FakeEvent(user, 2, "suspended")
    client = FakeClient(CapabilityDeliveryError("down", status_code=503))
    await DriverAccessStatusDispatcher(FakeQueue([first, second]), client).deliver_due(batch_size=10)
    assert client.sent == [first]  # the newer one waits while the older is not delivered
    assert second.status == "pending"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_nothing_is_sent_while_the_switch_is_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(driver_access_sync.settings, "driver_access_status_sync_enabled", False)
    client = FakeClient()
    await DriverAccessStatusDispatcher(FakeQueue([FakeEvent(uuid4(), 1)]), client).deliver_due(batch_size=10)
    assert client.sent == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_client_uses_its_own_scope_token_and_sends_the_status() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/service/token"):
            return httpx.Response(200, json={"access_token": "tok", "expires_in": 600})
        return httpx.Response(200, json={})

    client = IdentityCapabilityClient(base_url="http://id.test", client_id="diddigo", client_secret="s")
    client._client = httpx.AsyncClient(base_url="http://id.test", transport=httpx.MockTransport(handler))
    event = FakeEvent(uuid4(), 1)
    event.reason = "backfill_existing_driver"
    event.enabled_at = datetime(2026, 2, 1, 10, tzinfo=UTC)

    await client.send_driver_access_status(event, scope="capabilities:access:write")

    token_request, call = seen
    assert dict(httpx.QueryParams(token_request.content.decode()))["scope"] == "capabilities:access:write"
    assert call.method == "PATCH"
    assert call.url.path == f"/identity/v1/pro/internal/users/{event.user_id}/capabilities/diddigo/driver/access"
    assert call.headers["Idempotency-Key"] == event.event_id
    assert json.loads(call.content) == {
        "access_status": "enabled", "reason": "backfill_existing_driver", "event_id": event.event_id,
        "enabled_at": "2026-02-01T10:00:00Z",
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_client_without_a_scope_does_not_call(monkeypatch: pytest.MonkeyPatch) -> None:
    from app_base.modules.ride.infra import identity_capability_client as client_module

    monkeypatch.setattr(client_module.settings, "identity_driver_access_scope", None)
    calls: list = []
    client = IdentityCapabilityClient(base_url="http://id.test", client_id="diddigo", client_secret="s")
    client._client = httpx.AsyncClient(
        base_url="http://id.test", transport=httpx.MockTransport(lambda r: calls.append(r) or httpx.Response(200))
    )
    event = FakeEvent(uuid4(), 1)
    event.reason, event.enabled_at = "kyc_approved", None
    with pytest.raises(CapabilityDeliveryError) as excinfo:
        await client.send_driver_access_status(event, scope=None)
    assert excinfo.value.error_code == "IDENTITY_SERVICE_CREDENTIALS_MISSING"
    assert calls == []  # nothing sent, not even a token request


@pytest.mark.unit
def test_default_scope_is_the_diddifreeid_contract_one() -> None:
    from app_base.core.settings import settings

    assert settings.identity_driver_access_scope == "capabilities:access:write"
