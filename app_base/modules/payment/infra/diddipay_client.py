"""DiddiPay service-to-service HTTP client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
        if not self.configured:
            raise ApiError(
                503,
                ErrorCode.PAYMENT_CONFIGURATION_MISSING,
                "DiddiPay n'est pas configure pour cet environnement.",
            )

        url = f"{self.base_url.rstrip('/')}/payment-intents"
        headers = {
            "X-Client-ID": self.client_id,
            "X-Service-Key": self.service_key or "",
            "Idempotency-Key": idempotency_key,
        }
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
            try:
                body = response.json()
            except ValueError:
                body = {"raw": response.text[:500]}
            code = body.get("error", {}).get("code") if isinstance(body, dict) else None
            raise ApiError(
                response.status_code,
                code or ErrorCode.PAYMENT_OPERATION_CONFLICT,
                "DiddiPay a refuse l'operation de paiement.",
                {"provider": "diddipay", "response": body},
            )
        return response.json()
