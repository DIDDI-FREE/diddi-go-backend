from __future__ import annotations

import logging
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app_base.modules.notification.application import DeviceService, PushNotificationService
from app_base.modules.notification.domain import PushDeliveryError, UserDevice

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


async def test_invalid_token_disabled_and_other_devices_still_receive(caplog):
    repo = FakeDeviceRepo()
    user_id = uuid4()
    for token in ["old-invalid-token", "current-valid-token"]:
        await repo.upsert(UserDevice(uuid4(), user_id, "android", "fcm", token))
    gateway = FakeGateway()
    gateway.send = AsyncMock(side_effect=[PushDeliveryError("UNREGISTERED", invalid_token=True), None])
    service = PushNotificationService(repo, gateway)
    with caplog.at_level(logging.INFO):
        await service.send_ride_offer(driver_user_id=user_id, payload={"ride_id": "ride-1"})
    assert not repo.devices[0].enabled
    assert repo.devices[1].enabled
    assert gateway.send.await_count == 2
    assert '"event":"push.ride_offer.targets"' in caplog.text
    assert '"active_devices_count":2' in caplog.text
    assert '"event":"push.device.disabled"' in caplog.text
    assert '"provider_code":"UNREGISTERED"' in caplog.text
    assert "old-invalid-token" not in caplog.text
    gateway.send.reset_mock(side_effect=True)
    await service.send_ride_offer(driver_user_id=user_id, payload={"ride_id": "ride-2"})
    assert gateway.send.await_count == 1
    assert gateway.send.call_args.kwargs["token"] == "current-valid-token"


@pytest.mark.parametrize("error", [
    PushDeliveryError("UNAVAILABLE", status_code=503),
    PushDeliveryError("INVALID_ARGUMENT", status_code=400),
    RuntimeError("temporary failure"),
    PushDeliveryError("PUSH_DISABLED"),
])
async def test_other_failures_keep_device_and_are_not_reported_as_sent(error, caplog):
    repo = FakeDeviceRepo()
    user_id = uuid4()
    await repo.upsert(UserDevice(uuid4(), user_id, "android", "fcm", "keep-token"))
    gateway = FakeGateway()
    gateway.send = AsyncMock(side_effect=error)
    with caplog.at_level(logging.INFO):
        await PushNotificationService(repo, gateway).send_ride_offer(
            driver_user_id=user_id, payload={"ride_id": "ride-1"},
        )
    assert repo.devices[0].enabled
    assert '"event":"push.ride_offer.sent"' not in caplog.text


async def test_no_device_is_explained_in_logs(caplog):
    gateway = FakeGateway()
    with caplog.at_level(logging.INFO):
        await PushNotificationService(FakeDeviceRepo(), gateway).send_ride_offer(
            driver_user_id=uuid4(), payload={"ride_id": "ride-1"},
        )
    assert not gateway.sent
    assert "no_registered_device" in caplog.text
