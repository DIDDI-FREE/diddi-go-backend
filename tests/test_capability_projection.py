from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app_base.modules.ride.application.capability_projection import (
    DriverCapabilityProjectionDispatcher,
    DurableDriverCapabilityPublisher,
)
from app_base.modules.ride.domain.capability_projection import (
    DriverCapabilityProjectionEvent,
    DriverProjectionCandidate,
)
from app_base.modules.ride.infra.identity_capability_client import CapabilityDeliveryError

pytestmark = pytest.mark.unit


class FakeRepository:
    def __init__(self) -> None:
        self.events: list[DriverCapabilityProjectionEvent] = []
        self.succeeded: list[str] = []
        self.retries: list[tuple[str, str]] = []
        self.conflicts: list[str] = []
        self.refreshes = 0

    async def enqueue(self, user_id, *, operational_status, actions, request_id):
        if self.events and self.events[-1].operational_status == operational_status:
            return None
        version = len(self.events) + 1
        event = DriverCapabilityProjectionEvent(
            user_id=user_id,
            projection_version=version,
            operational_status=operational_status,
            actions=actions,
            event_id=f"evt-{version}",
        )
        self.events.append(event)
        return event

    async def list_due(self, *, now, limit):
        return self.events[:limit]

    async def mark_succeeded(self, event, *, now):
        self.succeeded.append(event.event_id)

    async def mark_retry(self, event, *, now, next_attempt_at, error):
        self.retries.append((event.event_id, error))

    async def mark_conflict(self, event, *, now, error):
        self.conflicts.append(event.event_id)

    async def schedule_stale_refresh(self, *, before, now, limit):
        return self.refreshes


class RecordingClient:
    def __init__(self, error: CapabilityDeliveryError | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, int]] = []

    async def send_driver_status(self, event):
        self.calls.append((event.event_id, event.projection_version))
        if self.error:
            raise self.error


async def test_publisher_deduplicates_unchanged_business_state() -> None:
    repository = FakeRepository()
    publisher = DurableDriverCapabilityPublisher(repository)  # type: ignore[arg-type]
    user_id = uuid4()

    assert await publisher.publish_driver_status(user_id, operational_status="online", actions=["go_offline"])
    assert await publisher.publish_driver_status(user_id, operational_status="online", actions=["go_offline"])

    assert [(event.event_id, event.projection_version) for event in repository.events] == [("evt-1", 1)]


async def test_network_retry_reuses_exact_event_and_version() -> None:
    repository = FakeRepository()
    user_id = uuid4()
    event = await repository.enqueue(
        user_id, operational_status="offline", actions=["go_online"], request_id="req-1",
    )
    client = RecordingClient(CapabilityDeliveryError("network down"))
    dispatcher = DriverCapabilityProjectionDispatcher(repository, client)  # type: ignore[arg-type]

    await dispatcher.deliver_due(batch_size=10)
    await dispatcher.deliver_due(batch_size=10)

    assert client.calls == [(event.event_id, event.projection_version)] * 2
    assert [item[0] for item in repository.retries] == [event.event_id, event.event_id]


async def test_conflict_is_not_retried_blindly() -> None:
    repository = FakeRepository()
    await repository.enqueue(uuid4(), operational_status="offline", actions=["go_online"], request_id=None)
    client = RecordingClient(
        CapabilityDeliveryError("version conflict", status_code=409, error_code="VERSION_CONFLICT", conflict=True),
    )
    dispatcher = DriverCapabilityProjectionDispatcher(repository, client)  # type: ignore[arg-type]

    await dispatcher.deliver_due(batch_size=10)

    assert repository.conflicts == ["evt-1"]
    assert repository.retries == []


async def test_success_marks_exact_persisted_event() -> None:
    repository = FakeRepository()
    event = await repository.enqueue(
        uuid4(), operational_status="pending_verification", actions=["await_kyc_review"], request_id=None,
    )
    client = RecordingClient()
    dispatcher = DriverCapabilityProjectionDispatcher(repository, client)  # type: ignore[arg-type]

    assert await dispatcher.deliver_due(batch_size=10) == 1
    assert repository.succeeded == [event.event_id]


async def test_reconciliation_enqueues_divergent_state_and_refreshes_stale_projection() -> None:
    repository = FakeRepository()
    repository.refreshes = 1
    user_id = uuid4()
    dispatcher = DriverCapabilityProjectionDispatcher(repository, RecordingClient())  # type: ignore[arg-type]

    result = await dispatcher.reconcile(
        candidates=[
            DriverProjectionCandidate(
                user_id=user_id,
                profile_status="active",
                vehicle_status="active",
                vehicle_active=True,
            ),
        ],
        online_user_ids={user_id},
        refresh_before=datetime.now(UTC),
        batch_size=10,
    )

    assert result == {"enqueued": 1, "refreshed": 1}
    assert repository.events[0].operational_status == "online"
    assert repository.events[0].actions == ["go_offline"]
