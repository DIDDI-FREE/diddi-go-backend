from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from app_base.modules.ride.application import emergency_notifications
from app_base.modules.ride.application.emergency_notifications import (
    EmergencyNotificationService,
    EmergencyRecipient,
    _evolution_number,
)
from app_base.shared_kernel.contracts.sms import SmsDelivery


def test_evolution_number_keeps_only_digits():
    assert _evolution_number("+237 699-11-11-11") == "237699111111"


@pytest.mark.asyncio
async def test_whatsapp_uses_evolution_send_text(monkeypatch):
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self, *, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, *, json, headers):
            captured.update(url=url, json=json, headers=headers)
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(emergency_notifications.settings, "evolution_api_url", "http://evolution.test/")
    monkeypatch.setattr(emergency_notifications.settings, "evolution_api_key", "secret")
    monkeypatch.setattr(emergency_notifications.settings, "evolution_instance", "DIDDI2")
    monkeypatch.setattr(emergency_notifications.settings, "evolution_api_timeout_seconds", 20.0)

    ride = SimpleNamespace(id="ride-1")
    recipient = EmergencyRecipient("support", "whatsapp", "+237699111111")
    payload = {
        "ride_id": "ride-1",
        "status": "in_progress",
        "actor_role": "passenger",
        "actor_user_id": "user-1",
        "passenger_user_id": "user-1",
        "driver_id": "driver-1",
        "pickup": {"lat": 5.3, "lng": -4.0, "address": "Pickup"},
        "dropoff": {"lat": 5.4, "lng": -3.9, "address": "Dropoff"},
        "note": "Urgence",
    }
    result = await EmergencyNotificationService()._send_whatsapp(
        ride,
        recipient,
        payload,
    )

    assert result["status"] == "sent"
    assert captured["url"] == "http://evolution.test/message/sendText/DIDDI2"
    assert captured["headers"]["apikey"] == "secret"
    assert captured["json"] == {
        "number": "237699111111",
        "text": emergency_notifications._human_message(payload),
    }
    assert captured["timeout"] == 20.0


class FakeSmsProvider:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def send(self, **kwargs) -> SmsDelivery:
        self.calls.append(kwargs)
        return SmsDelivery(provider="fake", status="queued", message_id="sms-1")

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_sms_uses_injected_provider():
    provider = FakeSmsProvider()
    service = EmergencyNotificationService(sms_provider=provider)
    ride = SimpleNamespace(id="ride-1")
    recipient = EmergencyRecipient("emergency_contact", "sms", "+2250700000000")
    payload = {
        "ride_id": "ride-1",
        "status": "in_progress",
        "actor_role": "passenger",
        "actor_user_id": "user-1",
        "passenger_user_id": "user-1",
        "driver_id": "driver-1",
        "pickup": {},
        "dropoff": {},
        "note": "Urgence",
    }

    result = await service._send_sms(ride, recipient, payload)

    assert result["status"] == "sent"
    assert result["provider"] == "fake"
    assert result["message_id"] == "sms-1"
    assert provider.calls[0]["idempotency_key"] == "diddigo-sos-ride-1-emergency_contact"
