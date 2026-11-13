from __future__ import annotations

import logging
from hashlib import sha256
from uuid import UUID

from app_base.core.observability import log_event
from app_base.modules.notification.domain import PushDeliveryError, PushGateway, UserDevice, UserDeviceRepository

logger = logging.getLogger("uvicorn.error")


class DeviceService:
    def __init__(self, devices: UserDeviceRepository) -> None:
        self.devices = devices

    async def register(
        self,
        *,
        user_id: UUID,
        platform: str,
        push_token: str,
        push_provider: str | None,
        device_id: str | None,
    ) -> dict:
        provider = push_provider or "fcm"
        device = await self.devices.upsert(
            UserDevice(
                id=UserDevice.new_id(),
                user_id=user_id,
                platform=platform,
                push_provider=provider,
                push_token=push_token,
                device_id=device_id,
            )
        )
        logger.info(
            "device_registered user_id=%s platform=%s provider=%s token_suffix=%s",
            user_id,
            platform,
            provider,
            push_token[-8:],
        )
        log_event(
            "push.device.registered",
            user_id=user_id,
            device_id=device.id,
            platform=platform,
            provider=provider,
            token_suffix=push_token[-8:],
        )
        return {
            "status": "registered",
            "id": str(device.id),
            "platform": device.platform,
            "push_provider": device.push_provider,
        }

    async def unregister(self, *, user_id: UUID, push_token: str) -> dict:
        await self.devices.disable(user_id=user_id, push_token=push_token)
        logger.info("device_unregistered user_id=%s token_suffix=%s", user_id, push_token[-8:])
        log_event("push.device.unregistered", user_id=user_id, token_suffix=push_token[-8:])
        return {"status": "unregistered"}


class PushNotificationService:
    def __init__(self, devices: UserDeviceRepository, gateway: PushGateway) -> None:
        self.devices = devices
        self.gateway = gateway

    async def send_ride_offer(self, *, driver_user_id: UUID, payload: dict) -> None:
        devices = await self.devices.active_for_user(driver_user_id)
        context = {"driver_user_id": driver_user_id, "ride_id": payload.get("ride_id")}
        log_event("push.ride_offer.targets", **context, active_devices_count=len(devices))
        if not devices:
            log_event("push.ride_offer.skipped", **context, reason="no_registered_device")
            return
        data = {
            "event": "ride.new_request",
            "ride_id": str(payload.get("ride_id", "")),
            "expires_in_seconds": str(payload.get("expires_in_seconds", "")),
        }
        for device in devices:
            target = {
                **context,
                "device_id": device.id,
                "platform": device.platform,
                "provider": device.push_provider,
                "token_fingerprint": sha256(device.push_token.encode()).hexdigest()[:16],
                "last_seen_at": device.last_seen_at,
            }
            if device.push_provider != "fcm":
                log_event("push.ride_offer.skipped", **target, reason="unsupported_provider")
                continue
            log_event("push.ride_offer.attempted", **target)
            try:
                await self.gateway.send(
                    token=device.push_token,
                    title="Nouvelle course DiddiGo",
                    body="Une course est disponible pres de vous.",
                    data=data,
                )
                log_event("push.ride_offer.sent", **target)
            except PushDeliveryError as exc:
                if exc.code == "PUSH_DISABLED":
                    log_event("push.ride_offer.skipped", **target, reason="push_disabled")
                    continue
                log_event(
                    "push.ride_offer.failed", level="error", **target,
                    provider_code=exc.code, status_code=exc.status_code, invalid_token=exc.invalid_token,
                )
                if exc.invalid_token:
                    await self.devices.disable(user_id=driver_user_id, push_token=device.push_token)
                    log_event("push.device.disabled", **target, reason=exc.code)
            except Exception as exc:
                # Do not log exception bodies: provider errors may contain tokens.
                log_event(
                    "push.ride_offer.failed", level="error", **target,
                    reason="gateway_error", error_type=type(exc).__name__, invalid_token=False,
                )
