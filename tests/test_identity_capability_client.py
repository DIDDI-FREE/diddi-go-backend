from __future__ import annotations

import json
from uuid import uuid4

import httpx
import pytest

from app_base.modules.ride.application.driver_service import _operational_status
from app_base.modules.ride.domain.entities import DriverProfile, DriverStatus, Vehicle, VehicleVerificationStatus
from app_base.modules.ride.infra.identity_capability_client import IdentityCapabilityClient

pytestmark = pytest.mark.unit


def _client(handler) -> IdentityCapabilityClient:
    client = IdentityCapabilityClient(
        base_url="https://identity.test",
        client_id="diddigo-staging-diddifreeid",
        client_secret="secret",
    )
    client._client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://identity.test")
    return client


async def test_publish_driver_status_gets_scoped_token_and_sends_projection() -> None:
    user_id = uuid4()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/auth/service/token"):
            assert request.headers["X-Client-ID"] == "diddigo-staging-diddifreeid"
            body = request.content.decode()
            assert "audience=diddifree-id" in body
            assert "scope=capabilities%3Awrite" in body
            return httpx.Response(200, json={"access_token": "service-token", "expires_in": 600})
        assert request.url.path == (
            f"/identity/v1/pro/internal/users/{user_id}/capabilities/diddigo/driver/status"
        )
        assert request.headers["Authorization"] == "Bearer service-token"
        payload = json.loads(request.content)
        expected_actions = {
            "online": ["go_offline"],
            "offline": ["go_online"],
        }
        assert payload["actions"] == expected_actions[payload["operational_status"]]
        assert payload["projection_version"] >= 1
        assert payload["event_id"].startswith(f"diddigo:driver:{user_id}:")
        return httpx.Response(200, json={"operational_status": payload["operational_status"]})

    client = _client(handler)
    try:
        assert await client.publish_driver_status(
            user_id,
            operational_status="online",
            actions=["go_offline"],
        )
        assert await client.publish_driver_status(
            user_id,
            operational_status="offline",
            actions=["go_online"],
        )
    finally:
        await client.close()

    assert len([request for request in requests if request.url.path.endswith("/auth/service/token")]) == 1


async def test_publish_driver_status_is_non_blocking_when_identity_is_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    client = _client(handler)
    try:
        result = await client.publish_driver_status(
            uuid4(),
            operational_status="unknown",
            actions=[],
        )
    finally:
        await client.close()

    assert result is False


async def test_publish_driver_status_skips_when_credentials_are_missing() -> None:
    client = IdentityCapabilityClient(base_url="https://identity.test", client_id=None, client_secret=None)

    assert await client.publish_driver_status(
        uuid4(),
        operational_status="offline",
        actions=["go_online"],
    ) is False


def test_driver_operational_status_remains_owned_by_diddigo() -> None:
    profile = DriverProfile(id=uuid4(), user_id=uuid4(), license_number="LIC-1", status=DriverStatus.ACTIVE)
    assert _operational_status(profile, None) == ("vehicle_missing", ["add_vehicle"])

    vehicle = Vehicle(
        id=uuid4(),
        driver_id=profile.id,
        plate_number="AB-123-CD",
        verification_status=VehicleVerificationStatus.ACTIVE,
        active=True,
    )
    assert _operational_status(profile, vehicle) == ("offline", ["go_online"])
