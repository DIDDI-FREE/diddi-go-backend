from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import OperationalError

from app_base.core.errors import infrastructure_error_handler, unhandled_exception_handler
from app_base.main import app

pytestmark = pytest.mark.unit


class FakeRedis:
    def __init__(self, *, ready: bool = True) -> None:
        self.ready = ready

    async def ping(self) -> bool:
        if not self.ready:
            raise RedisConnectionError("redis down")
        return True


@pytest.mark.asyncio
async def test_readiness_reports_all_dependencies_ready(monkeypatch) -> None:
    monkeypatch.setattr("app_base.main.database_ready", AsyncMock(return_value=True))
    app.state.redis = FakeRedis()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
    assert response.status_code == 200
    assert response.json()["components"] == {"database": "ok", "redis": "ok"}


@pytest.mark.asyncio
async def test_readiness_is_503_when_database_and_redis_are_down(monkeypatch) -> None:
    monkeypatch.setattr("app_base.main.database_ready", AsyncMock(return_value=False))
    app.state.redis = FakeRedis(ready=False)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["components"] == {"database": "unavailable", "redis": "unavailable"}


@pytest.mark.asyncio
async def test_database_failure_uses_contractual_json_error() -> None:
    test_app = FastAPI()
    test_app.add_exception_handler(OperationalError, infrastructure_error_handler)

    @test_app.get("/failure")
    async def failure():
        raise OperationalError("SELECT 1", {}, Exception("database down"))

    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/failure")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_unhandled_failure_never_returns_plain_text() -> None:
    test_app = FastAPI()
    test_app.add_exception_handler(Exception, unhandled_exception_handler)

    @test_app.get("/failure")
    async def failure():
        raise RuntimeError("unexpected")

    transport = httpx.ASGITransport(app=test_app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/failure")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
