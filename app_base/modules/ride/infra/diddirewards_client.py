"""DiddiRewards adapter for the explicit DiddiGo integration contract."""

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
class DiddiRewardsClient:
    base_url: str | None = settings.diddi_rewards_base_url
    client_id: str = settings.diddi_rewards_client_id
    service_token: str | None = settings.diddi_rewards_service_token
    client_secret: str | None = settings.diddi_rewards_service_client_secret
    identity_base_url: str | None = settings.identity_base_url
    timeout_seconds: float = settings.diddi_rewards_timeout_seconds
    service_scopes: str = settings.diddi_rewards_service_scopes
    transport: httpx.AsyncBaseTransport | None = None
    _token: tuple[str, float] | None = field(default=None, init=False, repr=False)
    _token_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and (self.service_token or (self.identity_base_url and self.client_secret)))

    async def validate_service_access(self) -> None:
        """Resolve one S2S token so mis-provisioned scopes fail at startup."""
        if not self.configured:
            raise ApiError(503, ErrorCode.PAYMENT_CONFIGURATION_MISSING, "Identifiants DiddiRewards absents.")
        await self._headers()

    async def quote(
        self,
        *,
        consumer_id: UUID,
        campaign_id: str | None,
        amount_initial_minor: int,
        request_id: str,
        honour_until: str | None = None,
    ) -> dict[str, Any]:
        """Quote a discount. Without `campaign_id` Rewards picks the customer's best offer (ticket 040).

        `honour_until` is DiddiGo's own quote expiry: until then Rewards gives the quoted
        discount at reserve when the answer's `quote_id` is sent back.
        """
        payload: dict[str, Any] = {
            "consumer_id": str(consumer_id),
            "service_code": "go",
            "amount_initial_minor": amount_initial_minor,
            "currency": "XOF",
        }
        if campaign_id:
            payload["campaign_id"] = campaign_id
        if honour_until:
            payload["honour_until"] = honour_until
        return await self._post(
            "/internal/v1/rewards/integrations/diddigo/benefits/quote",
            payload,
            request_id=request_id,
        )

    async def reserve(
        self,
        *,
        consumer_id: UUID,
        entitlement_id: UUID,
        ride_id: UUID,
        requested_amount_minor: int,
        idempotency_key: str,
        request_id: str,
        expires_at: str | None = None,
        quote_id: UUID | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "consumer_id": str(consumer_id),
            "entitlement_id": str(entitlement_id),
            "ride_id": str(ride_id),
            "requested_amount_minor": requested_amount_minor,
        }
        if expires_at:
            payload["expires_at"] = expires_at
        if quote_id:
            # Quote still valid: Rewards reserves the amount it stored at quote, not ours (ticket 040).
            payload["quote_id"] = str(quote_id)
        return await self._post(
            "/internal/v1/rewards/integrations/diddigo/benefits/reserve",
            payload,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    async def release(
        self,
        *,
        reservation_id: UUID,
        ride_id: UUID,
        reason: str,
        idempotency_key: str,
        request_id: str,
    ) -> dict[str, Any]:
        # Common release route shared by every service (ticket 016). The reservation is already
        # tied to the ride by its reserve Idempotency-Key, so `ride_id` is not sent any more.
        # Answer: 200 with the reservation; already released or expired gives `duplicate: true`.
        return await self._post(
            f"/internal/v1/rewards/integrations/diddigo/benefits/reservations/{reservation_id}/release",
            {"reason": reason[:180]},
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    async def confirm(
        self,
        *,
        reservation_id: UUID,
        ride_id: UUID,
        applied_discount_minor: int,
        client_paid_minor: int,
        driver_payout_minor: int,
        diddi_contribution_minor: int,
        payment_reference: str | None,
        idempotency_key: str,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._post(
            "/internal/v1/rewards/integrations/diddigo/benefits/confirm",
            {
                "reservation_id": str(reservation_id),
                "ride_id": str(ride_id),
                "applied_discount_minor": applied_discount_minor,
                "client_paid_minor": client_paid_minor,
                "driver_payout_minor": driver_payout_minor,
                "diddi_contribution_minor": diddi_contribution_minor,
                "payment_reference": payment_reference,
            },
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    async def correct(
        self,
        *,
        consumption_id: UUID,
        amount_minor: int,
        reason: str,
        payment_reference: str | None,
        idempotency_key: str,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._post(
            "/internal/v1/rewards/integrations/diddigo/benefits/correct",
            {
                "consumption_id": str(consumption_id),
                "amount_minor": amount_minor,
                "reason": reason,
                "payment_reference": payment_reference,
            },
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    async def reconciliation(
        self,
        *,
        consumption_id: UUID,
        confirmed_discount_minor: int,
        external_reference: str | None,
        details: dict[str, Any] | None,
        idempotency_key: str,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._post(
            "/internal/v1/rewards/integrations/diddigo/reconciliation",
            {
                "consumption_id": str(consumption_id),
                "confirmed_discount_minor": confirmed_discount_minor,
                "external_reference": external_reference,
                "details": details or {},
            },
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    async def consumer_offers(self, *, consumer_id: UUID, request_id: str) -> dict[str, Any]:
        """Every offer of the customer valid on rides, all states, history included (ticket 040)."""
        return await self._request(
            "GET",
            f"/internal/v1/rewards/integrations/diddigo/consumers/{consumer_id}/offers",
            None,
            request_id=request_id,
        )

    async def my_referral_code(self, *, consumer_id: UUID, request_id: str) -> dict[str, Any]:
        """The customer's own referral code; Rewards creates it on the first ask (ticket 040)."""
        return await self._request(
            "GET",
            f"/internal/v1/rewards/integrations/diddigo/consumers/{consumer_id}/referral-code",
            None,
            request_id=request_id,
        )

    async def apply_referral_code(
        self, *, consumer_id: UUID, code: str, idempotency_key: str, request_id: str
    ) -> dict[str, Any]:
        """A code typed by the customer. Rewards answers 200 accepted or refused (ticket 040)."""
        return await self._post(
            f"/internal/v1/rewards/integrations/diddigo/consumers/{consumer_id}/referral-code/apply",
            {"code": code},
            request_id=request_id,
            idempotency_key=idempotency_key,
        )

    async def _post(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        request_id: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return await self._request("POST", path, payload, request_id=request_id, idempotency_key=idempotency_key)

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        *,
        request_id: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not self.configured:
            raise ApiError(503, ErrorCode.PAYMENT_CONFIGURATION_MISSING, "DiddiRewards n'est pas configure.")
        headers = await self._headers()
        headers["X-Request-ID"] = request_id
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.request(
                    method, f"{self.base_url.rstrip('/')}{path}", json=payload, headers=headers
                )
        except httpx.HTTPError as exc:
            raise ApiError(503, "REWARDS_UNAVAILABLE", "DiddiRewards est indisponible.") from exc
        if response.status_code >= 400:
            try:
                body = response.json()
            except ValueError:
                body = {"raw": response.text[:500]}
            raise ApiError(response.status_code, "REWARDS_OPERATION_FAILED", "DiddiRewards a refuse l'operation.", body)
        if response.status_code == 204:
            return {}
        return response.json()

    async def _headers(self) -> dict[str, str]:
        token = self.service_token
        if not token and self.identity_base_url and self.client_secret:
            now = time.monotonic()
            if self._token and now < self._token[1]:
                token = self._token[0]
            else:
                async with self._token_lock:
                    now = time.monotonic()
                    if self._token and now < self._token[1]:
                        token = self._token[0]
                    else:
                        try:
                            async with httpx.AsyncClient(
                                base_url=self.identity_base_url.rstrip("/"),
                                timeout=self.timeout_seconds,
                                transport=self.transport,
                            ) as client:
                                response = await client.post(
                                    "/identity/v1/auth/service/token",
                                    headers={"X-Client-ID": self.client_id},
                                    data={
                                        "grant_type": "client_credentials",
                                        "client_id": self.client_id,
                                        "client_secret": self.client_secret,
                                        "audience": "diddirewards",
                                        "scope": self.service_scopes,
                                    },
                                )
                        except httpx.HTTPError as exc:
                            raise ApiError(
                                503, "REWARDS_UNAVAILABLE", "DiddiFreeID est injoignable pour le jeton DiddiRewards."
                            ) from exc
                        if response.status_code >= 400:
                            # 401 = identifiants ; 403 = audience ou scopes non autorises pour ce client
                            # (a corriger cote DiddiFreeID, pas ici).
                            try:
                                body = response.json()
                            except ValueError:
                                body = {"raw": response.text[:300]}
                            raise ApiError(
                                503,
                                "REWARDS_UNAVAILABLE",
                                "DiddiFreeID a refuse le jeton DiddiRewards (client, audience ou scopes).",
                                {
                                    "identity_status": response.status_code,
                                    "identity_error": body,
                                    "scope": self.service_scopes,
                                },
                            )
                        data = response.json()
                        token = str(data["access_token"])
                        self._token = (token, time.monotonic() + max(int(data.get("expires_in", 600)) - 30, 1))
        if not token:
            raise ApiError(503, ErrorCode.PAYMENT_CONFIGURATION_MISSING, "Identifiants DiddiRewards absents.")
        return {"Authorization": f"Bearer {token}", "X-Client-ID": self.client_id}
