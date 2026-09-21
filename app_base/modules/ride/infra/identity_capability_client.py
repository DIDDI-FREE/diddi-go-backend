from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from uuid import UUID

import httpx

from app_base.core.observability import current_request_id, log_event

logger = logging.getLogger(__name__)


@dataclass
class IdentityCapabilityClient:
    base_url: str | None
    client_id: str | None
    client_secret: str | None
    timeout_seconds: float = 5.0
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)
    _access_token: str | None = field(default=None, init=False, repr=False)
    _token_expires_at: float = field(default=0, init=False, repr=False)
    _token_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _last_projection_version: int = field(default=0, init=False, repr=False)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.client_id and self.client_secret)

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=(self.base_url or "http://identity-not-configured").rstrip("/"),
                timeout=self.timeout_seconds,
            )
        return self._client

    async def publish_driver_status(
        self,
        user_id: UUID,
        *,
        operational_status: str,
        actions: list[str],
    ) -> bool:
        if not self.configured:
            log_event(
                "identity.capability.publish.skipped",
                level="warning",
                user_id=user_id,
                service="diddigo",
                capability_type="driver",
                reason="identity_service_credentials_missing",
            )
            return False

        version = max(time.time_ns() // 1_000_000, self._last_projection_version + 1)
        self._last_projection_version = version
        event_id = f"diddigo:driver:{user_id}:{version}:{operational_status}"
        request_id = current_request_id()
        try:
            token = await self._service_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Client-ID": str(self.client_id),
            }
            if request_id:
                headers["X-Request-ID"] = request_id
            response = await self._http().patch(
                f"/identity/v1/pro/internal/users/{user_id}/capabilities/diddigo/driver/status",
                headers=headers,
                json={
                    "operational_status": operational_status,
                    "actions": actions,
                    "projection_version": version,
                    "event_id": event_id,
                },
            )
            response.raise_for_status()
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            logger.warning(
                "DiddiFreeID driver capability publication failed user_id=%s status=%s error=%s",
                user_id,
                operational_status,
                exc,
            )
            log_event(
                "identity.capability.publish.failed",
                level="error",
                user_id=user_id,
                service="diddigo",
                capability_type="driver",
                operational_status=operational_status,
                error_type=type(exc).__name__,
            )
            return False

        log_event(
            "identity.capability.publish.succeeded",
            user_id=user_id,
            service="diddigo",
            capability_type="driver",
            operational_status=operational_status,
            projection_version=version,
            event_id=event_id,
        )
        return True

    async def _service_token(self) -> str:
        now = time.monotonic()
        if self._access_token and now < self._token_expires_at:
            return self._access_token
        async with self._token_lock:
            now = time.monotonic()
            if self._access_token and now < self._token_expires_at:
                return self._access_token
            response = await self._http().post(
                "/identity/v1/auth/service/token",
                headers={"X-Client-ID": str(self.client_id)},
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "audience": "diddifree-id",
                    "scope": "capabilities:write",
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
