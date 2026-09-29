from __future__ import annotations

from uuid import uuid4

import httpx
import pytest

from app_base.modules.ride.infra.diddifiles_client import DiddiFilesClient

pytestmark = pytest.mark.unit


def _client(handler) -> DiddiFilesClient:
    return DiddiFilesClient(
        base_url="https://files.test",
        identity_base_url="https://identity.test",
        client_id="diddigo-staging-diddifiles",
        client_secret="secret",
        transport=httpx.MockTransport(handler),
    )


async def test_resolve_public_url_gets_a_scoped_token_and_returns_the_url() -> None:
    file_id = uuid4()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/auth/service/token"):
            assert request.headers["X-Client-ID"] == "diddigo-staging-diddifiles"
            body = request.content.decode()
            assert "audience=diddifiles" in body
            assert "scope=files%3Aread" in body
            return httpx.Response(200, json={"access_token": "service-token", "expires_in": 600})
        assert request.url.path == f"/v1/files/{file_id}/public-url"
        assert request.headers["Authorization"] == "Bearer service-token"
        return httpx.Response(200, json={"file_id": str(file_id), "public_url": "https://cdn.example/driver.jpg"})

    url = await _client(handler).resolve_public_url(file_id)
    assert url == "https://cdn.example/driver.jpg"
    assert len(requests) == 2


async def test_resolve_public_url_reuses_cached_token() -> None:
    token_requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal token_requests
        if request.url.path.endswith("/auth/service/token"):
            token_requests += 1
            return httpx.Response(200, json={"access_token": "service-token", "expires_in": 600})
        return httpx.Response(200, json={"public_url": "https://cdn.example/driver.jpg"})

    client = _client(handler)
    await client.resolve_public_url(uuid4())
    await client.resolve_public_url(uuid4())
    assert token_requests == 1


async def test_resolve_public_url_returns_none_when_file_not_public() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/service/token"):
            return httpx.Response(200, json={"access_token": "service-token", "expires_in": 600})
        return httpx.Response(409, json={"detail": "FILE_NOT_PUBLIC"})

    assert await _client(handler).resolve_public_url(uuid4()) is None


async def test_resolve_public_url_returns_none_when_diddifiles_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/service/token"):
            return httpx.Response(200, json={"access_token": "service-token", "expires_in": 600})
        raise httpx.ConnectError("connection refused", request=request)

    assert await _client(handler).resolve_public_url(uuid4()) is None


async def test_resolve_public_url_returns_none_when_file_id_is_none() -> None:
    def unreached(request: httpx.Request) -> httpx.Response:
        raise AssertionError("must not call DiddiFiles when there is no file id")

    client = DiddiFilesClient(
        base_url="https://files.test",
        identity_base_url="https://identity.test",
        client_id="diddigo-staging-diddifiles",
        client_secret="secret",
        transport=httpx.MockTransport(unreached),
    )
    assert await client.resolve_public_url(None) is None


async def test_resolve_public_url_returns_none_when_not_configured() -> None:
    def unreached(request: httpx.Request) -> httpx.Response:
        raise AssertionError("must not call DiddiFiles without configured credentials")

    client = DiddiFilesClient(
        base_url="https://files.test",
        identity_base_url=None,
        client_id=None,
        client_secret=None,
        transport=httpx.MockTransport(unreached),
    )
    assert await client.resolve_public_url(uuid4()) is None
