from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from uuid import UUID

import httpx


@dataclass
class DiddiFilesClient:
    """Resolves a durable public URL for a public-read DiddiFiles purpose.

    Authenticates with a DiddiFreeID client-credentials token
    (audience=diddifiles, scope=files:read), mirroring IdentityCapabilityClient's
    token caching. Never raises: a missing/private/unreachable file must not
    break the ride payload it enriches.
    """

    base_url: str | None
    identity_base_url: str | None
    client_id: str | None
    client_secret: str | None
    timeout_seconds: float = 5.0
    transport: httpx.AsyncBaseTransport | None = None
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)
    _access_token: str | None = field(default=None, init=False, repr=False)
    _token_expires_at: float = field(default=0, init=False, repr=False)
    _token_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.identity_base_url and self.client_id and self.client_secret)

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=(self.base_url or "http://diddifiles-not-configured").rstrip("/"),
                timeout=self.timeout_seconds,
                transport=self.transport,
            )
        return self._client

    async def resolve_public_url(self, file_id: UUID | None) -> str | None:
        if file_id is None or not self.configured:
            return None
        try:
            token = await self._service_token()
            response = await self._http().get(
                f"/v1/files/{file_id}/public-url",
                headers={"Authorization": f"Bearer {token}", "X-Client-ID": str(self.client_id)},
            )
            if response.status_code != 200:
                return None
            payload = response.json()
        except (httpx.HTTPError, ValueError, KeyError):
            return None
        return payload.get("public_url")

    async def _service_token(self) -> str:
        now = time.monotonic()
        if self._access_token and now < self._token_expires_at:
            return self._access_token
        async with self._token_lock:
            now = time.monotonic()
            if self._access_token and now < self._token_expires_at:
                return self._access_token
            async with httpx.AsyncClient(
                base_url=self.identity_base_url.rstrip("/"), timeout=self.timeout_seconds, transport=self.transport,
            ) as identity_client:
                response = await identity_client.post(
                    "/identity/v1/auth/service/token",
                    headers={"X-Client-ID": str(self.client_id)},
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "audience": "diddifiles",
                        "scope": "files:read",
                    },
                )
                response.raise_for_status()
                payload = response.json()
            token = payload["access_token"]
            if not isinstance(token, str) or not token:
                raise ValueError("DiddiFreeID token response has no access_token")
            expires_in = max(int(payload.get("expires_in", 600)), 1)
            self._access_token = token
            self._token_expires_at = time.monotonic() + max(expires_in - 30, 1)
            return token

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
