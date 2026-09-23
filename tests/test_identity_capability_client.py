from __future__ import annotations

import json
from uuid import uuid4

import httpx
import pytest

from app_base.modules.ride.application.driver_service import _operational_status
from app_base.modules.ride.domain.capability_projection import DriverCapabilityProjectionEvent
from app_base.modules.ride.domain.entities import DriverProfile, DriverStatus, Vehicle, VehicleVerificationStatus
from app_base.modules.ride.infra.identity_capability_client import CapabilityDeliveryError, IdentityCapabilityClient

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
        assert request.headers["X-Request-ID"] == "request-123"
        payload = json.loads(request.content)
        expected_actions = {
            "online": ["go_offline"],
            "offline": ["go_online"],
        }
        assert payload["actions"] == expected_actions[payload["operational_status"]]
        expected_versions = {"online": 41, "offline": 42}
        assert payload["projection_version"] == expected_versions[payload["operational_status"]]
        assert payload["event_id"] == f"evt-{payload['operational_status']}-{payload['projection_version']}"
        return httpx.Response(200, json={"operational_status": payload["operational_status"]})

    client = _client(handler)
    try:
        await client.send_driver_status(
            DriverCapabilityProjectionEvent(
                user_id=user_id,
                projection_version=41,
                operational_status="online",
                actions=["go_offline"],
                event_id="evt-online-41",
                request_id="request-123",
            ),
        )
        await client.send_driver_status(
            DriverCapabilityProjectionEvent(
                user_id=user_id,
                projection_version=42,
                operational_status="offline",
                actions=["go_online"],
                event_id="evt-offline-42",
                request_id="request-123",
            ),
        )
    finally:
        await client.close()

    assert len([request for request in requests if request.url.path.endswith("/auth/service/token")]) == 1


async def test_send_driver_status_classifies_409_as_projection_conflict() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/service/token"):
            return httpx.Response(200, json={"access_token": "service-token", "expires_in": 600})
        return httpx.Response(409, json={"error": {"code": "PROJECTION_VERSION_CONFLICT"}})

    client = _client(handler)
    try:
        with pytest.raises(CapabilityDeliveryError) as conflict:
            await client.send_driver_status(
                DriverCapabilityProjectionEvent(
                    user_id=uuid4(), projection_version=7, operational_status="offline",
                    actions=["go_online"], event_id="evt-7",
                ),
            )
    finally:
        await client.close()

    assert conflict.value.status_code == 409
    assert conflict.value.error_code == "PROJECTION_VERSION_CONFLICT"
    assert conflict.value.conflict is True


async def test_send_driver_status_reports_identity_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    client = _client(handler)
    try:
        with pytest.raises(CapabilityDeliveryError):
            await client.send_driver_status(
                DriverCapabilityProjectionEvent(
                    user_id=uuid4(), projection_version=1, operational_status="unknown",
                    actions=[], event_id="evt-1",
                ),
            )
    finally:
        await client.close()


async def test_send_driver_status_fails_when_credentials_are_missing() -> None:
    client = IdentityCapabilityClient(base_url="https://identity.test", client_id=None, client_secret=None)

    with pytest.raises(CapabilityDeliveryError):
        await client.send_driver_status(
            DriverCapabilityProjectionEvent(
                user_id=uuid4(), projection_version=1, operational_status="offline",
                actions=["go_online"], event_id="evt-1",
            ),
        )


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
