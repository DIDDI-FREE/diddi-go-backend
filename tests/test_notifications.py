from __future__ import annotations

from uuid import uuid4

import pytest

from app_base.modules.notification.application import DeviceService, PushNotificationService
from app_base.modules.notification.domain import UserDevice

pytestmark = pytest.mark.unit


class FakeDeviceRepo:
    def __init__(self) -> None:
        self.devices: list[UserDevice] = []

    async def upsert(self, device: UserDevice) -> UserDevice:
        self.devices = [stored for stored in self.devices if stored.push_token != device.push_token]
        self.devices.append(device)
        return device

    async def disable(self, *, user_id, push_token: str) -> None:
        for device in self.devices:
            if device.user_id == user_id and device.push_token == push_token:
                device.enabled = False

    async def active_for_user(self, user_id):
        return [device for device in self.devices if device.user_id == user_id and device.enabled]


class FakeGateway:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, *, token: str, title: str, body: str, data: dict[str, str]) -> None:
        self.sent.append({"token": token, "title": title, "body": body, "data": data})


@pytest.mark.asyncio
async def test_register_defaults_android_to_fcm() -> None:
    repo = FakeDeviceRepo()
    user_id = uuid4()

    result = await DeviceService(repo).register(
        user_id=user_id,
        platform="android",
        push_token="fcm-token-123",
        push_provider=None,
        device_id="device-1",
    )

    assert result["status"] == "registered"
    assert result["push_provider"] == "fcm"
    assert repo.devices[0].user_id == user_id


@pytest.mark.asyncio
async def test_register_defaults_ios_to_fcm() -> None:
    repo = FakeDeviceRepo()

    result = await DeviceService(repo).register(
        user_id=uuid4(),
        platform="ios",
        push_token="ios-fcm-token-123",
        push_provider=None,
        device_id="ios-device-1",
    )

    assert result["push_provider"] == "fcm"
    assert repo.devices[0].push_provider == "fcm"


@pytest.mark.asyncio
async def test_push_ride_offer_sends_to_fcm_devices_only() -> None:
    repo = FakeDeviceRepo()
    gateway = FakeGateway()
    user_id = uuid4()
    await repo.upsert(
        UserDevice(
            id=uuid4(),
            user_id=user_id,
            platform="android",
            push_provider="fcm",
            push_token="fcm-token-123",
        )
    )
    await repo.upsert(
        UserDevice(
            id=uuid4(),
            user_id=user_id,
            platform="ios",
            push_provider="apns",
            push_token="apns-token-123",
        )
    )

    await PushNotificationService(repo, gateway).send_ride_offer(
        driver_user_id=user_id,
        payload={"ride_id": "ride-1", "expires_in_seconds": 15},
    )

    assert len(gateway.sent) == 1
    assert gateway.sent[0]["token"] == "fcm-token-123"
    assert gateway.sent[0]["data"] == {
        "event": "ride.new_request",
        "ride_id": "ride-1",
        "expires_in_seconds": "15",
    }
