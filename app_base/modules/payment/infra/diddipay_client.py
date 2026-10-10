"""DiddiPay service-to-service HTTP client.

Auth: prefers a real DiddiFreeID service token (client_credentials, mirroring
DiddiFilesClient) whenever `diddipay_service_client_secret` is configured; falls back to the
legacy `X-Service-Key` shared secret otherwise. This lets the two rails coexist during
migration (SCRUM-504) — deploying this code changes nothing until the client_secret is actually
provisioned and set, at which point this client switches over on its own, no coordinated
redeploy with DiddiPay required.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import httpx

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.settings import settings


@dataclass
class DiddiPayClient:
    base_url: str | None = settings.diddipay_base_url
    identity_base_url: str | None = settings.identity_base_url
    client_id: str = settings.diddipay_client_id
    service_key: str | None = settings.diddipay_service_key
    client_secret: str | None = settings.diddipay_service_client_secret
    timeout_seconds: float = settings.diddipay_http_timeout_seconds
    transport: httpx.AsyncBaseTransport | None = None
    _scope_tokens: dict[str, tuple[str, float]] = field(default_factory=dict, init=False, repr=False)
    _token_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and (self.service_key or self._s2s_configured))

    @property
    def _s2s_configured(self) -> bool:
        return bool(self.identity_base_url and self.client_secret)

    async def create_payment_intent(self, payload: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        self._require_configured()

        url = f"{self.base_url.rstrip('/')}/payment-intents"
        headers = await self._headers(scope="diddipay:payment-intents:write", idempotency_key=idempotency_key)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise ApiError(
                503,
                ErrorCode.PAYMENT_PROVIDER_UNAVAILABLE,
                "DiddiPay est indisponible.",
            ) from exc

        if response.status_code >= 400:
            raise self._error_from(response)
        return response.json()

    async def get_payment_intent(self, payment_intent_id: UUID | str) -> dict[str, Any] | None:
        """Read back a PaymentIntent — the source of truth used by reconciliation.

        Returns None when DiddiPay does not know the intent (404): that is a
        data problem to report, not a transport failure to retry forever.
        """
        self._require_configured()

        url = f"{self.base_url.rstrip('/')}/payment-intents/{payment_intent_id}"
        headers = await self._headers(scope="diddipay:payment-intents:read")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            raise ApiError(
                503,
                ErrorCode.PAYMENT_PROVIDER_UNAVAILABLE,
                "DiddiPay est indisponible.",
            ) from exc

        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise self._error_from(response)
        return response.json()

    async def create_payout(self, payload: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        self._require_configured()
        url = f"{self.base_url.rstrip('/')}/payouts"
        headers = await self._headers(scope="diddipay:payouts:write", idempotency_key=idempotency_key)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise ApiError(503, ErrorCode.PAYMENT_PROVIDER_UNAVAILABLE, "DiddiPay est indisponible.") from exc
        if response.status_code >= 400:
            raise self._error_from(response)
        return response.json()

    async def get_payout(self, payout_id: UUID | str) -> dict[str, Any] | None:
        self._require_configured()
        url = f"{self.base_url.rstrip('/')}/payouts/{payout_id}"
        headers = await self._headers(scope="diddipay:payouts:read")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            raise ApiError(503, ErrorCode.PAYMENT_PROVIDER_UNAVAILABLE, "DiddiPay est indisponible.") from exc
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise self._error_from(response)
        return response.json()

    async def get_payout_by_business_reference(self, business_reference: str) -> dict[str, Any] | None:
        self._require_configured()
        url = f"{self.base_url.rstrip('/')}/payouts"
        headers = await self._headers(scope="diddipay:payouts:read")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.get(url, params={"business_reference": business_reference}, headers=headers)
        except httpx.HTTPError as exc:
            raise ApiError(503, ErrorCode.PAYMENT_PROVIDER_UNAVAILABLE, "DiddiPay est indisponible.") from exc
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise self._error_from(response)
        return response.json()

    def _require_configured(self) -> None:
        if not self.configured:
            raise ApiError(
                503,
                ErrorCode.PAYMENT_CONFIGURATION_MISSING,
                "DiddiPay n'est pas configure pour cet environnement.",
            )

    async def _headers(self, *, scope: str, idempotency_key: str | None = None) -> dict[str, str]:
        if self._s2s_configured:
            token = await self._service_token(scope)
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Client-ID": self.client_id,
            }
        else:
            headers = {
                "X-Client-ID": self.client_id,
                "X-Service-Key": self.service_key or "",
            }
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    async def _service_token(self, scope: str) -> str:
        now = time.monotonic()
        cached = self._scope_tokens.get(scope)
        if cached and now < cached[1]:
            return cached[0]
        async with self._token_lock:
            now = time.monotonic()
            cached = self._scope_tokens.get(scope)
            if cached and now < cached[1]:
                return cached[0]
            async with httpx.AsyncClient(
                base_url=self.identity_base_url.rstrip("/"),
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as identity_client:
                response = await identity_client.post(
                    "/identity/v1/auth/service/token",
                    headers={"X-Client-ID": str(self.client_id)},
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "audience": "diddipay",
                        "scope": scope,
                    },
                )
                response.raise_for_status()
                payload = response.json()
            token = payload["access_token"]
            if not isinstance(token, str) or not token:
                raise ValueError("DiddiFreeID token response has no access_token")
            expires_in = max(int(payload.get("expires_in", 600)), 1)
            self._scope_tokens[scope] = (
                token,
                time.monotonic() + max(expires_in - 30, 1),
            )
            return token

    @staticmethod
    def _error_from(response: httpx.Response) -> ApiError:
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text[:500]}
        code = body.get("error", {}).get("code") if isinstance(body, dict) else None
        return ApiError(
            response.status_code,
            code or ErrorCode.PAYMENT_OPERATION_CONFLICT,
            "DiddiPay a refuse l'operation de paiement.",
            {"provider": "diddipay", "response": body},
        )
