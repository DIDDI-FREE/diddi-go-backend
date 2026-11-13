from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx
import jwt

from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.notification.domain import PushDeliveryError

logger = logging.getLogger("uvicorn.error")

FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class FcmPushGateway:
    def __init__(self) -> None:
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    async def send(self, *, token: str, title: str, body: str, data: dict[str, str]) -> None:
        service_account = _load_service_account()
        project_id = settings.fcm_project_id or service_account.get("project_id")
        if not project_id:
            raise RuntimeError("FCM project id is not configured.")

        access_token = await self._access_token_for(service_account)
        url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
        payload = {
            "message": {
                "token": token,
                "notification": {"title": title, "body": body},
                "data": {key: str(value) for key, value in data.items()},
                "android": {"priority": "HIGH"},
            }
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if response.status_code >= 400:
            error = _delivery_error(response)
            log_event(
                "push.fcm.failed",
                level="error",
                project_id=project_id,
                token_suffix=token[-8:],
                status_code=response.status_code,
                provider_code=error.code,
                invalid_token=error.invalid_token,
            )
            raise error
        logger.info("push_fcm_sent project_id=%s token_suffix=%s", project_id, token[-8:])
        log_event("push.fcm.sent", project_id=project_id, token_suffix=token[-8:])

    async def _access_token_for(self, service_account: dict[str, Any]) -> str:
        now = int(time.time())
        if self._access_token and now < self._expires_at - 60:
            return self._access_token

        client_email = service_account["client_email"]
        private_key = service_account["private_key"]
        assertion = jwt.encode(
            {
                "iss": client_email,
                "scope": FCM_SCOPE,
                "aud": GOOGLE_TOKEN_URL,
                "iat": now,
                "exp": now + 3600,
            },
            private_key,
            algorithm="RS256",
        )
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
            )
        response.raise_for_status()
        payload = response.json()
        self._access_token = str(payload["access_token"])
        self._expires_at = now + int(payload.get("expires_in", 3600))
        return self._access_token


class DisabledPushGateway:
    async def send(self, *, token: str, title: str, body: str, data: dict[str, str]) -> None:
        logger.info("push_skipped_disabled provider=fcm token_suffix=%s title=%s", token[-8:], title)
        log_event(
            "push.fcm.skipped",
            provider="fcm",
            token_suffix=token[-8:],
            reason="push_disabled",
            title=title,
            data=data,
        )
        raise PushDeliveryError("PUSH_DISABLED")


def _delivery_error(response: httpx.Response) -> PushDeliveryError:
    """Only explicit token failures justify disabling a device.

    A generic 400/404 or INVALID_ARGUMENT may concern the payload/project.
    See https://firebase.google.com/docs/cloud-messaging/error-codes.
    """
    try:
        body = response.json()
    except ValueError:
        body = {}
    error = body.get("error", {}) if isinstance(body, dict) else {}
    if not isinstance(error, dict):
        error = {}
    details = error.get("details", [])
    details = details if isinstance(details, list) else []
    fcm_code = next((
        detail.get("errorCode") for detail in details
        if isinstance(detail, dict)
        and detail.get("@type") == "type.googleapis.com/google.firebase.fcm.v1.FcmError"
    ), None)
    token_invalid = fcm_code == "UNREGISTERED"
    # INVALID_ARGUMENT alone is ambiguous. Require the documented token-specific
    # diagnostic as well, without ever persisting its potentially sensitive text.
    if fcm_code == "INVALID_ARGUMENT" and error.get("message") == (
        "The registration token is not a valid FCM registration token"
    ):
        token_invalid = True
    code = fcm_code or error.get("status")
    if not isinstance(code, str) or not code.isupper() or len(code) > 64:
        code = "FCM_HTTP_ERROR"
    return PushDeliveryError(code, status_code=response.status_code, invalid_token=token_invalid)


def build_push_gateway():
    if not settings.push_enabled:
        return DisabledPushGateway()
    return FcmPushGateway()


def _load_service_account() -> dict[str, Any]:
    if settings.fcm_service_account_json:
        return json.loads(settings.fcm_service_account_json)
    if settings.fcm_service_account_file:
        return json.loads(Path(settings.fcm_service_account_file).read_text(encoding="utf-8"))
    raise RuntimeError("FCM service account is not configured.")
