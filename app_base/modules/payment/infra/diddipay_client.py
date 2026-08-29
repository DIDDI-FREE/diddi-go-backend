"""DiddiPay service-to-service HTTP client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.settings import settings


@dataclass
class DiddiPayClient:
    base_url: str | None = settings.diddipay_base_url
    client_id: str = settings.diddipay_client_id
    service_key: str | None = settings.diddipay_service_key
    timeout_seconds: float = 10.0

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.service_key)

    async def create_payment_intent(self, payload: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        self._require_configured()

        url = f"{self.base_url.rstrip('/')}/payment-intents"
        headers = self._headers(idempotency_key=idempotency_key)
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
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
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers())
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

    def _require_configured(self) -> None:
        if not self.configured:
            raise ApiError(
                503,
                ErrorCode.PAYMENT_CONFIGURATION_MISSING,
                "DiddiPay n'est pas configure pour cet environnement.",
            )

    def _headers(self, *, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {
            "X-Client-ID": self.client_id,
            "X-Service-Key": self.service_key or "",
        }
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return headers

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
