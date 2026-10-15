from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from app_base.shared_kernel.contracts.sms import SmsDelivery, SmsProvider


class SmsProviderError(RuntimeError):
    """A configured SMS provider rejected or could not process a message."""


@dataclass
class DisabledSmsProvider:
    async def send(
        self,
        *,
        recipient: str,
        message: str,
        idempotency_key: str,
    ) -> SmsDelivery:
        raise SmsProviderError("SMS provider is disabled")

    async def close(self) -> None:
        return None


@dataclass
class SenndoSmsProvider:
    api_key: str
    base_url: str = "https://api.senndo.com"
    sender: str | None = None
    timeout_seconds: float = 20.0
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url.rstrip("/"),
                timeout=self.timeout_seconds,
            )
        return self._client

    async def send(
        self,
        *,
        recipient: str,
        message: str,
        idempotency_key: str,
    ) -> SmsDelivery:
        body: dict[str, Any] = {
            "channel": "sms",
            "to": recipient,
            "text": message,
            "idempotencyKey": idempotency_key,
        }
        if self.sender:
            body["sender"] = self.sender
        response = await self._http().post(
            "/v1/messages",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Idempotency-Key": idempotency_key,
            },
            json=body,
        )
        await _raise_provider_error(response, "senndo")
        payload = _json_object(response)
        return SmsDelivery(
            provider="senndo",
            status=str(payload.get("status") or "accepted"),
            message_id=_first_string(payload, "id", "message_id", "messageId"),
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


@dataclass
class YellikaSmsProvider:
    api_token: str
    base_url: str = "https://panel.yellikasms.com"
    sender_id: str = "DiddiFree"
    timeout_seconds: float = 20.0
    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url.rstrip("/"),
                timeout=self.timeout_seconds,
            )
        return self._client

    async def send(
        self,
        *,
        recipient: str,
        message: str,
        idempotency_key: str,
    ) -> SmsDelivery:
        response = await self._http().post(
            "/api/v3/sms/send",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
                "Idempotency-Key": idempotency_key,
            },
            json={
                "recipient": recipient,
                "sender_id": self.sender_id,
                "type": "plain",
                "message": message,
            },
        )
        await _raise_provider_error(response, "yellika")
        payload = _json_object(response)
        if str(payload.get("status", "")).lower() in {"error", "failed"}:
            raise SmsProviderError(
                f"yellika SMS request failed: {_safe_error_code(payload)}",
            )
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        return SmsDelivery(
            provider="yellika",
            status=str(data.get("status") or payload.get("status") or "accepted"),
            message_id=_first_string(data, "id", "message_id", "messageId", "uid"),
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


def build_sms_provider(
    *,
    provider: str,
    senndo_api_key: str | None,
    senndo_base_url: str,
    senndo_sender: str | None,
    yellika_api_token: str | None,
    yellika_base_url: str,
    yellika_sender_id: str,
    timeout_seconds: float,
) -> SmsProvider:
    normalized = provider.strip().lower()
    if normalized in {"", "disabled", "none"}:
        return DisabledSmsProvider()
    if normalized == "senndo":
        if not senndo_api_key:
            raise RuntimeError("SMS_PROVIDER=senndo requires SENNDO_API_KEY")
        return SenndoSmsProvider(
            api_key=senndo_api_key,
            base_url=senndo_base_url,
            sender=senndo_sender,
            timeout_seconds=timeout_seconds,
        )
    if normalized == "yellika":
        if not yellika_api_token:
            raise RuntimeError("SMS_PROVIDER=yellika requires YELLIKA_API_TOKEN")
        return YellikaSmsProvider(
            api_token=yellika_api_token,
            base_url=yellika_base_url,
            sender_id=yellika_sender_id,
            timeout_seconds=timeout_seconds,
        )
    raise RuntimeError(f"Unsupported SMS_PROVIDER: {provider}")


async def _raise_provider_error(response: httpx.Response, provider: str) -> None:
    if response.is_success:
        return
    request_id = response.headers.get("x-request-id") or response.headers.get("x-correlation-id")
    detail = f" status={response.status_code}"
    if request_id:
        detail += f" request_id={request_id}"
    raise SmsProviderError(f"{provider} SMS request failed:{detail}")


def _json_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise SmsProviderError("SMS provider returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SmsProviderError("SMS provider returned an invalid payload")
    return payload


def _first_string(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _safe_error_code(payload: dict[str, Any]) -> str:
    code = payload.get("code") or payload.get("error_code")
    return str(code) if code else "provider_error"
