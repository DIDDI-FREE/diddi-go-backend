from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC

import httpx

from app_base.core.settings import settings
from app_base.modules.ride.domain.capability_projection import DriverCapabilityProjectionEvent

logger = logging.getLogger(__name__)


class CapabilityDeliveryError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        conflict: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.conflict = conflict


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
    _other_tokens: dict[str, tuple[str, float]] = field(default_factory=dict, init=False, repr=False)

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

    async def send_driver_status(self, event: DriverCapabilityProjectionEvent) -> None:
        if not self.configured:
            raise CapabilityDeliveryError(
                "DiddiFreeID service credentials are missing",
                error_code="IDENTITY_SERVICE_CREDENTIALS_MISSING",
            )
        try:
            token = await self._service_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Client-ID": str(self.client_id),
            }
            if event.request_id:
                headers["X-Request-ID"] = event.request_id
            response = await self._http().patch(
                f"/identity/v1/pro/internal/users/{event.user_id}/capabilities/diddigo/driver/status",
                headers=headers,
                json={
                    "operational_status": event.operational_status,
                    "actions": event.actions,
                    "projection_version": event.projection_version,
                    "event_id": event.event_id,
                },
            )
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            if isinstance(exc, httpx.HTTPStatusError):
                payload = _error_payload(exc.response)
                raise CapabilityDeliveryError(
                    f"DiddiFreeID returned HTTP {exc.response.status_code}",
                    status_code=exc.response.status_code,
                    error_code=payload,
                    conflict=exc.response.status_code == 409,
                ) from exc
            raise CapabilityDeliveryError(str(exc), error_code=type(exc).__name__) from exc
        if response.status_code >= 400:
            raise CapabilityDeliveryError(
                f"DiddiFreeID returned HTTP {response.status_code}",
                status_code=response.status_code,
                error_code=_error_payload(response),
                conflict=response.status_code == 409,
            )

    async def send_driver_access_status(self, event, *, scope: str | None = None) -> None:
        """Ticket 084: set the driver's access status in DiddiFreeID (`enabled`, `suspended`, `rejected`).

        Route of the DiddiFreeID contract (ticket 083, `main` `5e9aa28`): scope
        `capabilities:access:write`; the same `event_id` again answers 200 with no change.
        `enabled_at` is sent only by the one-time back-fill (the driver's real approval date);
        DiddiFreeID never uses it to replace a first validation date it already has.
        """
        scope = scope or settings.identity_driver_access_scope
        if not self.configured or not scope:
            raise CapabilityDeliveryError(
                "DiddiFreeID service credentials or IDENTITY_DRIVER_ACCESS_SCOPE are missing",
                error_code="IDENTITY_SERVICE_CREDENTIALS_MISSING",
            )
        body = {"access_status": event.access_status, "reason": event.reason, "event_id": event.event_id}
        if event.enabled_at is not None:
            body["enabled_at"] = event.enabled_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
        try:
            token = await self._service_token(scope)
            response = await self._http().patch(
                f"/identity/v1/pro/internal/users/{event.user_id}/capabilities/diddigo/driver/access",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Client-ID": str(self.client_id),
                    "Idempotency-Key": event.event_id,
                    "X-Request-ID": event.event_id,
                },
                json=body,
            )
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            if isinstance(exc, httpx.HTTPStatusError):
                raise CapabilityDeliveryError(
                    f"DiddiFreeID returned HTTP {exc.response.status_code}",
                    status_code=exc.response.status_code,
                    error_code=_error_payload(exc.response),
                ) from exc
            raise CapabilityDeliveryError(str(exc), error_code=type(exc).__name__) from exc
        if response.status_code >= 400:
            raise CapabilityDeliveryError(
                f"DiddiFreeID returned HTTP {response.status_code}",
                status_code=response.status_code,
                error_code=_error_payload(response),
            )

    async def _service_token(self, scope: str = "capabilities:write") -> str:
        if scope != "capabilities:write":
            return await self._scoped_token(scope)
        now = time.monotonic()
        if self._access_token and now < self._token_expires_at:
            return self._access_token
        async with self._token_lock:
            now = time.monotonic()
            if self._access_token and now < self._token_expires_at:
                return self._access_token
            token, expires_at = await self._request_token(scope)
            self._access_token = token
            self._token_expires_at = expires_at
            return token

    async def _scoped_token(self, scope: str) -> str:
        """A token for another scope, cached apart: a missing grant never breaks capabilities:write."""
        cached = self._other_tokens.get(scope)
        if cached and time.monotonic() < cached[1]:
            return cached[0]
        async with self._token_lock:
            cached = self._other_tokens.get(scope)
            if cached and time.monotonic() < cached[1]:
                return cached[0]
            token, expires_at = await self._request_token(scope)
            self._other_tokens[scope] = (token, expires_at)
            return token

    async def _request_token(self, scope: str) -> tuple[str, float]:
        response = await self._http().post(
            "/identity/v1/auth/service/token",
            headers={"X-Client-ID": str(self.client_id)},
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "audience": "diddifree-id",
                "scope": scope,
            },
        )
        response.raise_for_status()
        payload = response.json()
        token = payload["access_token"]
        if not isinstance(token, str) or not token:
            raise ValueError("DiddiFreeID token response has no access_token")
        expires_in = max(int(payload.get("expires_in", 600)), 1)
        return token, time.monotonic() + max(expires_in - 30, 1)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def _error_payload(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        return str(error.get("code") or "") or None
    return str(payload.get("detail") or "") or None if isinstance(payload, dict) else None
