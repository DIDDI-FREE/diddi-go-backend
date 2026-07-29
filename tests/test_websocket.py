"""WebSocket tests — authentication, event multiplexing, and fan-out.

Uses Starlette's TestClient, which drives the ASGI app in a worker thread and
supports the WebSocket handshake (httpx's ASGITransport does not).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app_base.core.redis import create_redis_pool
from app_base.core.security import issue_access_token, issue_refresh_token
from app_base.core.settings import settings
from app_base.modules.ride.infra.driver_location import RedisDriverLocationService
from app_base.modules.ride.presentation.websocket import WS_UNAUTHORIZED

ABIDJAN = {"lat": 5.3599, "lng": -4.0083}


@pytest.fixture
def ws_client(database):
    """Synchronous TestClient for WebSocket tests.

    `TestClient` as a context manager runs the app's real lifespan, which
    creates the Redis pool on entry and closes it on exit. Because `app` is a
    module-level singleton, a pool closed by one test would poison the next —
    so each test enters the lifespan fresh and the engine is disposed after,
    matching what the async `client` fixture does.
    """
    import anyio

    from app_base.core.database import engine
    from app_base.main import app

    with TestClient(app) as client:
        yield client

    anyio.run(engine.dispose)


def driver_token() -> str:
    return issue_access_token(uuid4(), "driver")


def passenger_token() -> str:
    return issue_access_token(uuid4(), "passenger")


# --- authentication --------------------------------------------------------

def test_connection_without_a_token_is_refused(ws_client) -> None:
    with pytest.raises(WebSocketDisconnect) as excinfo, ws_client.websocket_connect("/v1/ws"):
        pass
    assert excinfo.value.code == WS_UNAUTHORIZED


def test_connection_with_a_garbage_token_is_refused(ws_client) -> None:
    with pytest.raises(WebSocketDisconnect) as excinfo, ws_client.websocket_connect("/v1/ws?token=not-a-jwt"):
        pass
    assert excinfo.value.code == WS_UNAUTHORIZED


def test_connection_with_a_refresh_token_is_refused(ws_client) -> None:
    """Only access tokens open a socket — the `typ` claim is enforced."""
    refresh = issue_refresh_token(uuid4())
    with pytest.raises(WebSocketDisconnect) as excinfo, ws_client.websocket_connect(f"/v1/ws?token={refresh}"):
        pass
    assert excinfo.value.code == WS_UNAUTHORIZED


def test_valid_access_token_connects(ws_client) -> None:
    with ws_client.websocket_connect(f"/v1/ws?token={passenger_token()}") as ws:
        ws.send_json({"event": "ping"})
        assert ws.receive_json() == {"event": "ignored", "received_event": "ping"}


# --- driver.location_push --------------------------------------------------

def test_driver_location_push_is_acknowledged(ws_client) -> None:
    with ws_client.websocket_connect(f"/v1/ws?token={driver_token()}") as ws:
        ws.send_json({"event": "driver.location_push", "location": ABIDJAN, "heading": 134})
        assert ws.receive_json() == {"event": "ack", "received_event": "driver.location_push"}


def test_passenger_cannot_push_a_driver_location(ws_client) -> None:
    with ws_client.websocket_connect(f"/v1/ws?token={passenger_token()}") as ws:
        ws.send_json({"event": "driver.location_push", "location": ABIDJAN})
        assert ws.receive_json() == {"event": "error", "code": "FORBIDDEN_ROLE"}


def test_location_push_without_coordinates_is_rejected(ws_client) -> None:
    with ws_client.websocket_connect(f"/v1/ws?token={driver_token()}") as ws:
        ws.send_json({"event": "driver.location_push", "location": {"lat": 5.3}})
        assert ws.receive_json() == {"event": "error", "code": "INVALID_LOCATION"}


def test_location_push_writes_through_to_redis(ws_client) -> None:
    """The push must land in the Redis GEO set, not just be acknowledged."""
    import anyio

    user_id = uuid4()
    token = issue_access_token(user_id, "driver")
    with ws_client.websocket_connect(f"/v1/ws?token={token}") as ws:
        ws.send_json({"event": "driver.location_push", "location": ABIDJAN})
        ws.receive_json()

        async def read_position():
            redis = create_redis_pool(settings.redis_url)
            service = RedisDriverLocationService(redis=redis)
            try:
                return await service.get_position(user_id)
            finally:
                await redis.aclose()

        position = anyio.run(read_position)

    assert position is not None
    assert position.lat == pytest.approx(ABIDJAN["lat"], abs=1e-4)


# --- ride.subscribe + fan-out ----------------------------------------------

def test_ride_subscribe_is_acknowledged(ws_client) -> None:
    ride_id = str(uuid4())
    with ws_client.websocket_connect(f"/v1/ws?token={passenger_token()}") as ws:
        ws.send_json({"event": "ride.subscribe", "ride_id": ride_id})
        assert ws.receive_json() == {
            "event": "ack", "received_event": "ride.subscribe", "ride_id": ride_id,
        }


def test_ride_subscribe_rejects_a_bad_uuid(ws_client) -> None:
    with ws_client.websocket_connect(f"/v1/ws?token={passenger_token()}") as ws:
        ws.send_json({"event": "ride.subscribe", "ride_id": "not-a-uuid"})
        assert ws.receive_json() == {"event": "error", "code": "INVALID_RIDE_ID"}


def test_driver_location_reaches_a_subscribed_passenger(ws_client) -> None:
    """The core fan-out the contract promises: a driver pushing their position
    on a ride is delivered to whoever is watching that ride."""
    ride_id = str(uuid4())

    with ws_client.websocket_connect(f"/v1/ws?token={passenger_token()}") as passenger:
        passenger.send_json({"event": "ride.subscribe", "ride_id": ride_id})
        passenger.receive_json()  # ack

        with ws_client.websocket_connect(f"/v1/ws?token={driver_token()}") as driver:
            driver.send_json(
                {
                    "event": "driver.location_push",
                    "ride_id": ride_id,
                    "location": {"lat": 5.3601, "lng": -4.0090},
                    "heading": 134,
                }
            )
            driver.receive_json()  # ack

        broadcast = passenger.receive_json()

    assert broadcast["event"] == "ride.driver_location"
    assert broadcast["ride_id"] == ride_id
    assert broadcast["location"] == {"lat": 5.3601, "lng": -4.0090}
    assert broadcast["heading"] == 134
    assert broadcast["at"].endswith("Z")


def test_unsubscribed_sockets_do_not_receive_other_rides(ws_client) -> None:
    watched = str(uuid4())
    other = str(uuid4())

    with ws_client.websocket_connect(f"/v1/ws?token={passenger_token()}") as passenger:
        passenger.send_json({"event": "ride.subscribe", "ride_id": watched})
        passenger.receive_json()

        with ws_client.websocket_connect(f"/v1/ws?token={driver_token()}") as driver:
            driver.send_json(
                {"event": "driver.location_push", "ride_id": other, "location": ABIDJAN},
            )
            driver.receive_json()

            # Prove the passenger's queue is empty by round-tripping a ping.
            passenger.send_json({"event": "ping"})
            assert passenger.receive_json() == {"event": "ignored", "received_event": "ping"}


def test_unknown_events_are_ignored_not_fatal(ws_client) -> None:
    """The contract says clients must tolerate unknown events; the server
    holds the same contract in reverse so new client versions can't kill it."""
    with ws_client.websocket_connect(f"/v1/ws?token={passenger_token()}") as ws:
        ws.send_json({"event": "some.future.event", "payload": {"anything": True}})
        assert ws.receive_json() == {"event": "ignored", "received_event": "some.future.event"}

        ws.send_json({"event": "ping"})
        assert ws.receive_json()["event"] == "ignored"
