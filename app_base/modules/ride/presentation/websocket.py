"""WebSocket endpoint — one multiplexed socket per app session.

API contract §4: clients connect once to `/v1/ws?token=<access_token>` and
everything is dispatched on `event.type`, rather than opening a socket per
channel. The server never replays missed events — after a reconnect the
client re-reads `GET /rides/{id}` to resynchronise.

Events, server → passenger:
    ride.status_changed    {ride_id, status, at}
    ride.driver_location   {ride_id, location, heading, at}
    ride.no_driver_found   {ride_id}

Events, server → driver:
    ride.new_request       {ride_id, pickup, dropoff_address, vehicle_category,
                            comfort_level, payment_method, expires_in_seconds}

Events, client → server:
    driver.location_push   {location: {lat, lng}, heading}
    ride.subscribe         {ride_id}   — passenger follows one ride

Dispatching a `ride.new_request` to drivers belongs to the matching engine,
which is deferred (architecture doc §7 step 3). `ConnectionManager` already
exposes the send methods that engine will call.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app_base.core.database import async_session_factory
from app_base.core.errors import ApiError
from app_base.core.identity import (
    decode_identity_access_token,
    identity_mode_enabled,
    user_id_from_identity_payload,
)
from app_base.core.observability import log_event
from app_base.core.security import decode_token, user_id_from_token
from app_base.modules.ride.domain.entities import DriverStatus
from app_base.modules.ride.infra.repositories import SqlAlchemyDriverProfileRepository
from app_base.shared_kernel.types import GeoPoint

# Uvicorn wires this logger to the Docker console.
logger = logging.getLogger("uvicorn.error")

router = APIRouter(tags=["ride-ws"])

# Close codes (RFC 6455 application range).
WS_UNAUTHORIZED = 4401


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class ConnectionManager:
    """Tracks live sockets so the server can address a specific passenger,
    driver, or everyone watching one ride.

    Kept in process memory: correct for the single-process deployment the
    architecture doc specifies today. When a second app instance appears,
    this becomes a Redis pub/sub fan-out — the call sites stay identical.
    """

    def __init__(self) -> None:
        self._by_user: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._by_ride: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._sockets: dict[WebSocket, UUID] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID) -> None:
        await websocket.accept()
        self._by_user[user_id].add(websocket)
        self._sockets[websocket] = user_id

    def disconnect(self, websocket: WebSocket) -> None:
        user_id = self._sockets.pop(websocket, None)
        if user_id is not None:
            self._by_user[user_id].discard(websocket)
            if not self._by_user[user_id]:
                del self._by_user[user_id]
        for ride_id, sockets in list(self._by_ride.items()):
            sockets.discard(websocket)
            if not sockets:
                del self._by_ride[ride_id]

    def subscribe_to_ride(self, websocket: WebSocket, ride_id: UUID) -> None:
        self._by_ride[ride_id].add(websocket)

    async def send_to_user(self, user_id: UUID, payload: dict[str, Any]) -> None:
        sockets = self._by_user.get(user_id, set())
        logger.info(
            "ws_send_to_user user_id=%s socket_count=%s event=%s",
            user_id,
            len(sockets),
            payload.get("event"),
        )
        log_event("ws.send_to_user", user_id=user_id, socket_count=len(sockets), ws_event=payload.get("event"))
        await self._fan_out(sockets, payload)

    async def send_to_ride(self, ride_id: UUID, payload: dict[str, Any]) -> None:
        sockets = self._by_ride.get(ride_id, set())
        logger.info(
            "ws_send_to_ride ride_id=%s socket_count=%s event=%s",
            ride_id,
            len(sockets),
            payload.get("event"),
        )
        log_event("ws.send_to_ride", ride_id=ride_id, socket_count=len(sockets), ws_event=payload.get("event"))
        await self._fan_out(sockets, payload)

    async def _fan_out(self, sockets: set[WebSocket], payload: dict[str, Any]) -> None:
        for websocket in list(sockets):
            try:
                await websocket.send_json(payload)
            except (WebSocketDisconnect, RuntimeError):
                # The peer vanished mid-send; drop it and keep serving the rest.
                self.disconnect(websocket)

    # -- typed helpers used by the service layer ----------------------------

    async def broadcast_status_changed(self, ride_id: UUID, status: str) -> None:
        await self.send_to_ride(
            ride_id,
            {"event": "ride.status_changed", "ride_id": str(ride_id), "status": status, "at": _now_iso()},
        )

    async def broadcast_driver_location(
        self, ride_id: UUID, location: GeoPoint, heading: int | None = None,
    ) -> None:
        await self.send_to_ride(
            ride_id,
            {
                "event": "ride.driver_location",
                "ride_id": str(ride_id),
                "location": {"lat": location.lat, "lng": location.lng},
                "heading": heading,
                "at": _now_iso(),
            },
        )

    async def broadcast_no_driver_found(self, ride_id: UUID) -> None:
        await self.send_to_ride(
            ride_id, {"event": "ride.no_driver_found", "ride_id": str(ride_id)},
        )

    async def send_new_request(self, driver_user_id: UUID, payload: dict[str, Any]) -> None:
        """Used by the matching engine (deferred) to offer a ride to a driver."""
        logger.info(
            "ws_send_new_request driver_user_id=%s ride_id=%s socket_count=%s",
            driver_user_id,
            payload.get("ride_id"),
            len(self._by_user.get(driver_user_id, set())),
        )
        log_event(
            "ws.ride_offer.sent",
            driver_user_id=driver_user_id,
            ride_id=payload.get("ride_id"),
            socket_count=len(self._by_user.get(driver_user_id, set())),
        )
        await self.send_to_user(driver_user_id, {"event": "ride.new_request", **payload})


manager = ConnectionManager()


@router.get("/ws", status_code=426)
def websocket_upgrade_required() -> dict[str, Any]:
    """Helpful diagnostic when a proxy/client sends plain HTTP to the socket.

    A proper WebSocket request reaches `websocket_endpoint`; a normal GET would
    otherwise be a confusing 404 because HTTP and WebSocket routes are distinct
    ASGI scopes.
    """
    return {
        "code": "WEBSOCKET_UPGRADE_REQUIRED",
        "message": "Use ws:// or wss:// with an Upgrade: websocket handshake.",
        "path": "/v1/ws?token=<access_token>",
    }


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """Single multiplexed socket. The access token arrives as a query
    parameter because browsers cannot set headers on a WebSocket handshake."""
    if not token:
        await websocket.close(code=WS_UNAUTHORIZED, reason="Missing token")
        return
    try:
        user_id, role = _decode_ws_access_token(token)
    except ApiError as exc:
        logger.warning(
            "ws_auth_failed client_ip=%s code=%s path=%s",
            _ws_client_ip(websocket),
            exc.code,
            websocket.url.path,
        )
        log_event("ws.auth_failed", level="warning", client_ip=_ws_client_ip(websocket), error_code=exc.code)
        await websocket.close(code=WS_UNAUTHORIZED, reason=exc.code)
        return

    connection_id = str(uuid4())
    await manager.connect(websocket, user_id)
    logger.info(
        "ws_connected connection_id=%s user_id=%s role=%s client_ip=%s path=%s",
        connection_id,
        user_id,
        role,
        _ws_client_ip(websocket),
        websocket.url.path,
    )
    log_event(
        "ws.connected",
        connection_id=connection_id,
        user_id=user_id,
        role=role,
        client_ip=_ws_client_ip(websocket),
        path=websocket.url.path,
    )

    # The driver location service lives on app.state (mounted by the lifespan).
    locations = getattr(websocket.app.state, "driver_locations", None)

    try:
        while True:
            message = await websocket.receive_json()
            await _handle_message(websocket, message, user_id=user_id, role=role, locations=locations)
    except WebSocketDisconnect:
        logger.info("ws_disconnected connection_id=%s user_id=%s role=%s", connection_id, user_id, role)
        log_event("ws.disconnected", connection_id=connection_id, user_id=user_id, role=role)
    except Exception:
        logger.exception("ws_failed connection_id=%s user_id=%s role=%s", connection_id, user_id, role)
        log_event("ws.failed", level="error", connection_id=connection_id, user_id=user_id, role=role)
    finally:
        if role == "driver" and locations is not None:
            await locations.go_offline(user_id)
        manager.disconnect(websocket)


def _decode_ws_access_token(token: str) -> tuple[UUID, str]:
    if identity_mode_enabled():
        payload = decode_identity_access_token(token)
        return user_id_from_identity_payload(payload), _normalise_role(payload.get("role"))

    payload = decode_token(token, expected_typ="access")
    return user_id_from_token(payload), _normalise_role(payload.get("role"))


def _normalise_role(role: object) -> str:
    return "passenger" if role in {None, "user"} else str(role)


async def _handle_message(
    websocket: WebSocket,
    message: Any,
    *,
    user_id: UUID,
    role: str,
    locations: Any,
) -> None:
    if not isinstance(message, dict):
        await websocket.send_json({"event": "error", "code": "MALFORMED_MESSAGE"})
        return

    event = message.get("event")

    if event == "driver.location_push":
        if role not in {"admin", "driver"} and not await _has_active_driver_profile(user_id):
            await websocket.send_json({"event": "error", "code": "FORBIDDEN_ROLE"})
            return
        location = _parse_location(message.get("location"))
        if location is None:
            await websocket.send_json({"event": "error", "code": "INVALID_LOCATION"})
            return
        if locations is not None:
            await locations.update_position(user_id, location)
        ride_id = message.get("ride_id")
        if ride_id:
            try:
                await manager.broadcast_driver_location(
                    UUID(str(ride_id)), location, message.get("heading"),
                )
            except ValueError:
                await websocket.send_json({"event": "error", "code": "INVALID_RIDE_ID"})
                return
        await websocket.send_json({"event": "ack", "received_event": event})
        logger.info("ws_driver_location_push user_id=%s ride_id=%s", user_id, ride_id)
        log_event("ws.driver_location.received", user_id=user_id, ride_id=ride_id, role=role)
        return

    if event == "ride.subscribe":
        try:
            ride_id = UUID(str(message.get("ride_id")))
        except (TypeError, ValueError):
            await websocket.send_json({"event": "error", "code": "INVALID_RIDE_ID"})
            return
        manager.subscribe_to_ride(websocket, ride_id)
        await websocket.send_json(
            {"event": "ack", "received_event": event, "ride_id": str(ride_id)},
        )
        logger.info("ws_ride_subscribe user_id=%s role=%s ride_id=%s", user_id, role, ride_id)
        log_event("ws.ride_subscribed", user_id=user_id, role=role, ride_id=ride_id)
        return

    # Unknown events are acknowledged and ignored rather than fatal — the
    # contract lets the API add event types without breaking older clients.
    await websocket.send_json({"event": "ignored", "received_event": event})


def _parse_location(raw: Any) -> GeoPoint | None:
    if not isinstance(raw, dict):
        return None
    try:
        return GeoPoint(lat=float(raw["lat"]), lng=float(raw["lng"]))
    except (KeyError, TypeError, ValueError):
        return None


def _ws_client_ip(websocket: WebSocket) -> str | None:
    forwarded_for = websocket.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    real_ip = websocket.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return websocket.client.host if websocket.client else None


async def _has_active_driver_profile(user_id: UUID) -> bool:
    async with async_session_factory() as session:
        profile = await SqlAlchemyDriverProfileRepository(session).find_by_user_id(user_id)
    return profile is not None and profile.status is DriverStatus.ACTIVE
