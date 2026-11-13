import logging
from unittest.mock import AsyncMock

import httpx
import pytest

from app_base.modules.notification.domain import PushDeliveryError
from app_base.modules.notification.infra import fcm

pytestmark = pytest.mark.unit
FCM_TYPE = "type.googleapis.com/google.firebase.fcm.v1.FcmError"


@pytest.mark.parametrize(("status", "error", "invalid"), [
    (404, {"status": "NOT_FOUND", "details": [{"@type": FCM_TYPE, "errorCode": "UNREGISTERED"}]}, True),
    (400, {"status": "INVALID_ARGUMENT", "message": "The registration token is not a valid FCM registration token",
           "details": [{"@type": FCM_TYPE, "errorCode": "INVALID_ARGUMENT"}]}, True),
    (400, {"status": "INVALID_ARGUMENT", "details": [{"@type": FCM_TYPE, "errorCode": "INVALID_ARGUMENT"}]}, False),
    (400, {"status": "INVALID_ARGUMENT", "details": [{"@type": "type.googleapis.com/google.rpc.BadRequest"}]}, False),
    (404, {"status": "NOT_FOUND"}, False),
    (403, {"details": [{"@type": FCM_TYPE, "errorCode": "SENDER_ID_MISMATCH"}]}, False),
    (429, {"status": "QUOTA_EXCEEDED"}, False),
    (503, {"status": "UNAVAILABLE"}, False),
    (401, {"status": "UNAUTHENTICATED"}, False),
    (500, None, False),
])
def test_only_explicit_token_errors_disable_devices(status, error, invalid):
    failure = fcm._delivery_error(httpx.Response(status, json={"error": error}))
    assert failure.invalid_token is invalid
    assert failure.status_code == status


def test_non_json_provider_error_is_safe():
    failure = fcm._delivery_error(httpx.Response(502, text="<html>upstream failed</html>"))
    assert failure.code == "FCM_HTTP_ERROR"
    assert not failure.invalid_token


async def test_gateway_classifies_response_and_does_not_log_sensitive_body(monkeypatch, caplog):
    token = "private-registration-token-never-log-in-full"
    real_client = httpx.AsyncClient

    def respond(request):
        assert token in request.content.decode()
        return httpx.Response(404, json={"error": {
            "message": token,
            "details": [{"@type": FCM_TYPE, "errorCode": "UNREGISTERED"}],
        }})

    monkeypatch.setattr(fcm, "_load_service_account", lambda: {"project_id": "test-project"})
    monkeypatch.setattr(fcm.httpx, "AsyncClient", lambda **kwargs: real_client(
        transport=httpx.MockTransport(respond), **kwargs,
    ))
    gateway = fcm.FcmPushGateway()
    monkeypatch.setattr(gateway, "_access_token_for", AsyncMock(return_value="test-access-token"))
    with caplog.at_level(logging.INFO), pytest.raises(PushDeliveryError) as error:
        await gateway.send(token=token, title="test", body="test", data={})
    assert error.value.invalid_token
    assert token not in caplog.text


async def test_disabled_gateway_never_reports_success():
    with pytest.raises(PushDeliveryError, match="PUSH_DISABLED"):
        await fcm.DisabledPushGateway().send(token="token", title="test", body="test", data={})
