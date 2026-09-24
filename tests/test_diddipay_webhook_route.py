"""Route-level regression tests for POST /internal/webhooks/diddipay.

The service layer was already covered, but the route itself was not: the
handler returned the injected Response without a status code, which made the
request-logging middleware crash after processing and turned every processed
webhook into a 500 for DiddiPay (events dead-lettered despite being applied).
"""

from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from app_base.core.deps import payment_service
from app_base.core.request_logging import RequestLoggingMiddleware
from app_base.modules.payment.presentation.router import internal_router

pytestmark = pytest.mark.unit


class StubPaymentService:
    def __init__(self, status: str) -> None:
        self.status = status

    async def apply_diddipay_webhook(self, *, raw_body, event_id_header, signature):
        return {"status": self.status}


def make_app(status: str) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(internal_router)
    app.dependency_overrides[payment_service] = lambda: StubPaymentService(status)
    return app


async def post_webhook(app: FastAPI) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(
            "/internal/webhooks/diddipay",
            content=b"{}",
            headers={
                "X-DiddiPay-Event-ID": "evt_route_test",
                "X-DiddiPay-Signature": "sig",
            },
        )


@pytest.mark.asyncio
async def test_processed_webhook_returns_204_through_logging_middleware() -> None:
    response = await post_webhook(make_app("processed"))

    assert response.status_code == 204
    assert response.headers.get("X-Request-ID")


@pytest.mark.asyncio
async def test_duplicate_webhook_returns_200_through_logging_middleware() -> None:
    response = await post_webhook(make_app("duplicate"))

    assert response.status_code == 200
