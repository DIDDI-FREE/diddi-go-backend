from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app_base.core.auth_deps import get_current_user
from app_base.core.deps import ride_service
from app_base.core.errors import ApiError, api_error_handler, request_validation_error_handler
from app_base.modules.ride.application.services import RideService
from app_base.modules.ride.domain.entities import RideStatus
from app_base.modules.ride.infra.repositories import SqlAlchemyRideRepository
from app_base.modules.ride.presentation import router as routes
from app_base.modules.ride.presentation.websocket import ConnectionManager
from tests.test_ride_authorization_service import (
    DRIVER_USER_ID,
    OTHER_USER_ID,
    PASSENGER_ID,
    FakeDriverRepo,
    FakeRideRepo,
    matched_ride,
)

pytestmark = pytest.mark.unit


class StopsRepo(FakeRideRepo):
    def __init__(self, ride):
        super().__init__(ride)
        self.stops = []
        self.commits = 0

    async def list_stops(self, ride_id):
        return [stop for stop in self.stops if stop.ride_id == ride_id]

    async def add_stop(self, stop):
        stop.sequence = len(self.stops)
        self.stops.append(stop)
        return stop

    async def commit(self):
        self.commits += 1


@pytest.fixture
def stops_service():
    ride = matched_ride()
    ride.status = RideStatus.IN_PROGRESS
    ride.estimated_fare = Decimal("2500")
    ride.distance_km = Decimal("7")
    ride.actual_distance_km = Decimal("0.1")
    repo = StopsRepo(ride)
    service = RideService(ride_repo=repo, routing=None, pricing_rules=None, driver_repo=FakeDriverRepo())
    return service, repo, ride


async def add(service, ride, user_id=PASSENGER_ID):
    return await service.add_stop(
        ride.id, actor_user_id=user_id, actor_role="user",
        latitude=5.36, longitude=-4.01, address=" Plateau ", note="Pharmacie",
    )


@pytest.mark.parametrize("actor", [PASSENGER_ID, DRIVER_USER_ID])
async def test_participants_add_stops_without_changing_fare(stops_service, actor):
    service, repo, ride = stops_service
    result = await add(service, ride, actor)
    assert result["address"] == "Plateau"
    assert result["sequence"] == 0
    assert repo.commits == 1
    assert ride.estimated_fare == Decimal("2500")
    assert ride.final_fare is None
    assert ride.distance_km == Decimal("7")
    assert ride.actual_distance_km == Decimal("0.1")
    assert ride.supplements_total == 0


async def test_unrelated_user_cannot_add_stop(stops_service):
    service, repo, ride = stops_service
    with pytest.raises(ApiError) as error:
        await add(service, ride, OTHER_USER_ID)
    assert error.value.status_code == 403
    assert repo.stops == []
    assert repo.commits == 0


@pytest.mark.parametrize("status", [RideStatus.MATCHED, RideStatus.COMPLETED, RideStatus.CANCELLED_BY_PASSENGER])
async def test_cannot_add_stop_outside_active_trip(stops_service, status):
    service, repo, ride = stops_service
    ride.status = status
    with pytest.raises(ApiError) as error:
        await add(service, ride)
    assert error.value.code == "RIDE_NOT_ACTIVE"
    assert repo.stops == []


async def test_waiting_ride_accepts_stop(stops_service):
    service, _, ride = stops_service
    ride.status = RideStatus.WAITING
    assert (await add(service, ride))["sequence"] == 0


async def test_detail_and_recovery_return_ordered_stops_for_both_participants(stops_service):
    service, _, ride = stops_service
    first = await add(service, ride)
    second = await add(service, ride, DRIVER_USER_ID)
    for actor, role in [(PASSENGER_ID, "passenger"), (DRIVER_USER_ID, "driver")]:
        detail = await service.get_ride(ride.id, actor_user_id=actor, actor_role=role)
        recovered = await service.get_active_ride(actor_user_id=actor, actor_role=role)
        assert detail["stops"] == recovered["stops"] == [first, second]


async def test_http_add_commits_before_broadcast_and_list_contract(stops_service, monkeypatch):
    service, repo, ride = stops_service
    app = FastAPI()
    app.include_router(routes.router, prefix="/v1")
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.dependency_overrides[ride_service] = lambda: service
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=PASSENGER_ID, role="user")

    async def after_commit(ride_id, payload):
        assert repo.commits == 1
        assert payload["id"] == str(repo.stops[0].id)

    broadcast = AsyncMock(side_effect=after_commit)
    monkeypatch.setattr(routes.manager, "broadcast_stop_added", broadcast)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
        response = await client.post(f"/v1/rides/{ride.id}/stops", json={
            "latitude": 5.36, "longitude": -4.01, "address": "Plateau",
        })
        assert response.status_code == 201
        broadcast.assert_awaited_once()
        detail = (await client.get(f"/v1/rides/{ride.id}")).json()
        recovery = (await client.get("/v1/rides/active/current")).json()
        assert detail["stops"] == recovery["stops"] == [response.json()]
        history = (await client.get("/v1/rides")).json()
        row = history["data"][0]
        assert row["planned_distance_km"] == 7
        assert row["actual_distance_km"] == 0.1
        assert row["currency"] == "XOF"
        assert row["pickup_address"] is None
        assert row["pickup"]["address"] is None
        bad = await client.post(f"/v1/rides/{ride.id}/stops", json={"address": "text only"})
        assert bad.status_code == 422
        assert broadcast.await_count == 1


async def test_event_reaches_both_subscribers_but_not_another_ride():
    manager = ConnectionManager()
    passenger, driver, unrelated = AsyncMock(), AsyncMock(), AsyncMock()
    ride_id = uuid4()
    manager.subscribe_to_ride(passenger, ride_id)
    manager.subscribe_to_ride(driver, ride_id)
    manager.subscribe_to_ride(unrelated, uuid4())
    await manager.broadcast_stop_added(ride_id, {"id": "stop-1"})
    for socket in [passenger, driver]:
        socket.send_json.assert_awaited_once()
        event = socket.send_json.call_args.args[0]
        assert event["event"] == "ride.stop_added"
        assert event["ride_id"] == str(ride_id)
    unrelated.send_json.assert_not_awaited()


@pytest.mark.parametrize(("pickup", "dropoff"), [(None, None), ("  ", ""), (" Cocody ", "Plateau")])
async def test_history_addresses_are_preserved_or_null_not_invented(stops_service, pickup, dropoff):
    service, _, ride = stops_service
    ride.pickup_address, ride.dropoff_address = pickup, dropoff
    ride.actual_distance_km = None
    result = await service.list_rides(actor_user_id=PASSENGER_ID, actor_role="user")
    row = result["data"][0]
    assert row["pickup_address"] == row["pickup"]["address"] == ((pickup or "").strip() or None)
    assert row["dropoff_address"] == row["dropoff"]["address"] == ((dropoff or "").strip() or None)
    assert row["actual_distance_km"] is None
    assert row["planned_distance_km"] == 7


async def test_sql_append_locks_ride_before_allocating_sequence(stops_service):
    service, repo, ride = stops_service
    await add(service, ride)
    stop = repo.stops[0]
    session = SimpleNamespace(
        execute=AsyncMock(side_effect=[
            SimpleNamespace(scalar_one_or_none=lambda: "in_progress"),
            SimpleNamespace(scalar_one_or_none=lambda: 4),
        ]), add=lambda row: None, flush=AsyncMock(),
    )
    result = await SqlAlchemyRideRepository(session).add_stop(stop)
    assert result.sequence == 5
    assert "FOR UPDATE" in str(session.execute.call_args_list[0].args[0])
    session.flush.assert_awaited_once()


async def test_sql_append_rejects_ride_completed_while_waiting_for_lock(stops_service):
    service, repo, ride = stops_service
    await add(service, ride)
    session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: "completed")))
    with pytest.raises(ApiError, match="RIDE_NOT_ACTIVE"):
        await SqlAlchemyRideRepository(session).add_stop(repo.stops[0])
    assert session.execute.await_count == 1


async def test_sql_reads_stops_in_sequence_order_and_scopes_to_ride(stops_service):
    service, repo, ride = stops_service
    await add(service, ride)
    session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(
        scalars=lambda: SimpleNamespace(all=lambda: repo.stops),
    )))
    stops = await SqlAlchemyRideRepository(session).list_stops(ride.id)
    assert stops == repo.stops
    query = session.execute.call_args.args[0]
    assert str(query).endswith(
        "ORDER BY ride.ride_stops.sequence, ride.ride_stops.created_at, ride.ride_stops.id"
    )
    assert ride.id in query.compile().params.values()


async def test_quote_missing_address_is_null_and_diagnostic_has_no_address_text(caplog):
    import logging

    from app_base.shared_kernel.types import GeoPoint
    from tests.test_ride_quote_service import service_with_repositories

    service, quotes, _ = service_with_repositories()
    with caplog.at_level(logging.INFO):
        await service.create_quote(
            passenger_user_id=PASSENGER_ID,
            pickup=GeoPoint(lat=5.35, lng=-4.01), pickup_address="  ",
            dropoff=GeoPoint(lat=5.32, lng=-4.02), dropoff_address=" Private address ",
            vehicle_category="standard", comfort_level="standard",
        )
    quote = next(iter(quotes.quotes.values()))
    assert quote.pickup_address is None
    assert quote.dropoff_address == "Private address"
    assert '"pickup_address_present":false' in caplog.text
    assert '"dropoff_address_present":true' in caplog.text
    assert "Private address" not in caplog.text

