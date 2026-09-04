from __future__ import annotations

import json
import logging
from uuid import uuid4

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

from app_base.core.observability import bind_request_id, log_event, reset_request_id
from app_base.core.request_logging import RequestLoggingMiddleware

pytestmark = pytest.mark.unit


def test_log_event_emits_json_with_bound_request_id(caplog) -> None:
    request_id = "req-test-123"
    user_id = uuid4()
    token = bind_request_id(request_id)
    try:
        with caplog.at_level(logging.INFO, logger="uvicorn.error"):
            log_event("ride.test_event", user_id=user_id, nested={"ok": True})
    finally:
        reset_request_id(token)

    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "ride.test_event"
    assert payload["request_id"] == request_id
    assert payload["user_id"] == str(user_id)
    assert payload["nested"] == {"ok": True}


@pytest.mark.asyncio
async def test_request_logging_middleware_adds_request_id_header(caplog) -> None:
    async def app(request: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    middleware = RequestLoggingMiddleware(app)
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/v1/test",
        "headers": [(b"x-request-id", b"req-client-1"), (b"user-agent", b"pytest")],
        "query_string": b"token=secret&q=abc",
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "root_path": "",
    }
    request = Request(scope, receive=_empty_receive)

    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        response = await middleware.dispatch(request, app)

    assert response.headers["X-Request-ID"] == "req-client-1"
    payload = json.loads(caplog.records[-1].message)
    assert payload["event"] == "http.request"
    assert payload["request_id"] == "req-client-1"
    assert payload["path"] == "/v1/test"
    assert payload["query"] == "token=%2A%2A%2A&q=abc"


async def _empty_receive() -> dict:
    return {"type": "http.request", "body": b"", "more_body": False}
