from __future__ import annotations

import logging
from uuid import UUID

from app_base.modules.notification.domain import PushGateway, UserDevice, UserDeviceRepository

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
        return {
            "status": "registered",
            "id": str(device.id),
            "platform": device.platform,
            "push_provider": device.push_provider,
        }

    async def unregister(self, *, user_id: UUID, push_token: str) -> dict:
        await self.devices.disable(user_id=user_id, push_token=push_token)
        logger.info("device_unregistered user_id=%s token_suffix=%s", user_id, push_token[-8:])
        return {"status": "unregistered"}


class PushNotificationService:
    def __init__(self, devices: UserDeviceRepository, gateway: PushGateway) -> None:
        self.devices = devices
        self.gateway = gateway

    async def send_ride_offer(self, *, driver_user_id: UUID, payload: dict) -> None:
        devices = await self.devices.active_for_user(driver_user_id)
        if not devices:
            logger.info("push_ride_offer_skipped driver_user_id=%s reason=no_registered_device", driver_user_id)
            return

        data = {
            "event": "ride.new_request",
            "ride_id": str(payload.get("ride_id", "")),
            "expires_in_seconds": str(payload.get("expires_in_seconds", "")),
        }
        for device in devices:
            if device.push_provider != "fcm":
                logger.warning(
                    "push_ride_offer_skipped driver_user_id=%s device_id=%s provider=%s reason=fcm_only",
                    driver_user_id,
                    device.id,
                    device.push_provider,
                )
                continue
            try:
                await self.gateway.send(
                    token=device.push_token,
                    title="Nouvelle course DiddiGo",
                    body="Une course est disponible pres de vous.",
                    data=data,
                )
                logger.info(
                    "push_ride_offer_sent driver_user_id=%s device_id=%s provider=%s ride_id=%s",
                    driver_user_id,
                    device.id,
                    device.push_provider,
                    payload.get("ride_id"),
                )
            except Exception:
                logger.exception(
                    "push_ride_offer_failed driver_user_id=%s device_id=%s provider=%s ride_id=%s",
                    driver_user_id,
                    device.id,
                    device.push_provider,
                    payload.get("ride_id"),
                )
