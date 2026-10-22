from uuid import uuid4

import pytest
from starlette.testclient import TestClient

from app_base.core.security import issue_access_token
from app_base.main import app
from app_base.modules.ride.presentation import websocket as ws_module

pytestmark = pytest.mark.unit


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.messages.append(payload)


def test_plain_http_get_to_ws_returns_upgrade_required():
    response = TestClient(app).get("/v1/ws")

    assert response.status_code == 426
    assert response.json()["code"] == "WEBSOCKET_UPGRADE_REQUIRED"


def test_websocket_local_token_decoder_keeps_driver_role(monkeypatch):
    user_id = uuid4()
    monkeypatch.setattr(ws_module, "identity_mode_enabled", lambda: False)

    decoded_user_id, role = ws_module._decode_ws_access_token(issue_access_token(user_id, "driver"))

    assert decoded_user_id == user_id
    assert role == "driver"


def test_websocket_identity_token_decoder_maps_user_to_passenger(monkeypatch):
    user_id = uuid4()
    monkeypatch.setattr(ws_module, "identity_mode_enabled", lambda: True)
    monkeypatch.setattr(
        ws_module,
        "decode_identity_access_token",
        lambda token: {"sub": str(user_id), "role": "user", "status": "active"},
    )

    decoded_user_id, role = ws_module._decode_ws_access_token("identity-token")

    assert decoded_user_id == user_id
    assert role == "passenger"


@pytest.mark.asyncio
async def test_ping_receives_a_pong_without_touching_business_state() -> None:
    websocket = FakeWebSocket()

    await ws_module._handle_message(
        websocket,
        {"event": "ping"},
        user_id=uuid4(),
        role="passenger",
        locations=None,
    )

    assert websocket.messages[0]["event"] == "pong"
    assert websocket.messages[0]["at"].endswith("Z")
