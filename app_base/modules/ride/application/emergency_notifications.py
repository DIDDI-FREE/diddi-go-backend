from __future__ import annotations

import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any

import httpx

from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.ride.domain.entities import EmergencyContact, Ride


@dataclass(frozen=True)
class EmergencyRecipient:
    target: str
    channel: str
    recipient: str | None


class EmergencyNotificationService:
    async def notify(
        self,
        *,
        ride: Ride,
        actor_user_id: Any,
        actor_role: str,
        contact: EmergencyContact | None,
        note: str | None,
    ) -> list[dict]:
        payload = _emergency_payload(
            ride=ride,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            note=note,
        )
        recipients = [
            EmergencyRecipient("support", "email", settings.emergency_support_email),
            EmergencyRecipient("support", "whatsapp", settings.emergency_support_whatsapp),
        ]
        if contact is not None:
            recipients.extend(
                [
                    EmergencyRecipient("emergency_contact", "email", contact.email),
                    EmergencyRecipient("emergency_contact", "whatsapp", contact.phone),
                ]
            )
        else:
            log_event(
                "ride.emergency.notification.skipped",
                level="warning",
                ride_id=ride.id,
                channel="contact",
                target="emergency_contact",
                reason="emergency_contact_missing",
            )

        results: list[dict] = []
        for recipient in recipients:
            if not recipient.recipient:
                results.append(await self._skip(ride, recipient, "recipient_missing"))
                continue
            if recipient.channel == "email":
                results.append(await self._send_email(ride, recipient, payload))
            elif recipient.channel == "whatsapp":
                results.append(await self._send_whatsapp(ride, recipient, payload))
        return results

    async def _send_whatsapp(self, ride: Ride, recipient: EmergencyRecipient, payload: dict) -> dict:
        if not settings.emergency_whatsapp_webhook_url:
            return await self._skip(ride, recipient, "whatsapp_webhook_not_configured")
        headers = {"Content-Type": "application/json"}
        if settings.emergency_whatsapp_api_key:
            headers["Authorization"] = f"Bearer {settings.emergency_whatsapp_api_key}"
        body = {
            "to": recipient.recipient,
            "template": "diddigo_emergency_alert",
            "message": _human_message(payload),
            "data": payload,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.emergency_notification_timeout_seconds) as client:
                response = await client.post(settings.emergency_whatsapp_webhook_url, json=body, headers=headers)
                response.raise_for_status()
        except Exception as exc:
            return self._failed(ride, recipient, str(exc))
        return self._sent(ride, recipient)

    async def _send_email(self, ride: Ride, recipient: EmergencyRecipient, payload: dict) -> dict:
        if not settings.emergency_smtp_host:
            return await self._skip(ride, recipient, "smtp_not_configured")
        try:
            await asyncio.to_thread(_send_smtp_email, recipient.recipient, payload)
        except Exception as exc:
            return self._failed(ride, recipient, str(exc))
        return self._sent(ride, recipient)

    async def _skip(self, ride: Ride, recipient: EmergencyRecipient, reason: str) -> dict:
        result = _result(recipient, "skipped", reason=reason)
        log_event(
            "ride.emergency.notification.skipped",
            level="warning",
            ride_id=ride.id,
            target=recipient.target,
            channel=recipient.channel,
            recipient=recipient.recipient,
            reason=reason,
        )
        return result

    def _sent(self, ride: Ride, recipient: EmergencyRecipient) -> dict:
        result = _result(recipient, "sent")
        log_event(
            "ride.emergency.notification.sent",
            ride_id=ride.id,
            target=recipient.target,
            channel=recipient.channel,
            recipient=recipient.recipient,
        )
        return result

    def _failed(self, ride: Ride, recipient: EmergencyRecipient, error: str) -> dict:
        result = _result(recipient, "failed", reason=error)
        log_event(
            "ride.emergency.notification.failed",
            level="error",
            ride_id=ride.id,
            target=recipient.target,
            channel=recipient.channel,
            recipient=recipient.recipient,
            error=error,
        )
        return result


def _send_smtp_email(to_email: str | None, payload: dict) -> None:
    if not to_email:
        return
    message = EmailMessage()
    message["Subject"] = f"Urgence DiddiGo - course {payload['ride_id']}"
    message["From"] = settings.emergency_email_from
    message["To"] = to_email
    message.set_content(_human_message(payload))
    with smtplib.SMTP(settings.emergency_smtp_host, settings.emergency_smtp_port, timeout=10) as smtp:
        if settings.emergency_smtp_use_tls:
            smtp.starttls()
        if settings.emergency_smtp_username and settings.emergency_smtp_password:
            smtp.login(settings.emergency_smtp_username, settings.emergency_smtp_password)
        smtp.send_message(message)


def _emergency_payload(*, ride: Ride, actor_user_id: Any, actor_role: str, note: str | None) -> dict:
    return {
        "ride_id": str(ride.id),
        "status": ride.status.value,
        "actor_user_id": str(actor_user_id),
        "actor_role": actor_role,
        "passenger_user_id": str(ride.passenger_user_id),
        "driver_id": str(ride.driver_id) if ride.driver_id else None,
        "vehicle_id": str(ride.vehicle_id) if ride.vehicle_id else None,
        "pickup": {
            "lat": ride.pickup_location.lat if ride.pickup_location else None,
            "lng": ride.pickup_location.lng if ride.pickup_location else None,
            "address": ride.pickup_address,
        },
        "dropoff": {
            "lat": ride.dropoff_location.lat if ride.dropoff_location else None,
            "lng": ride.dropoff_location.lng if ride.dropoff_location else None,
            "address": ride.dropoff_address,
        },
        "note": note,
    }


def _human_message(payload: dict) -> str:
    return (
        "Alerte urgence DiddiGo\n"
        f"Course: {payload['ride_id']}\n"
        f"Statut: {payload['status']}\n"
        f"Declencheur: {payload['actor_role']} {payload['actor_user_id']}\n"
        f"Passager: {payload['passenger_user_id']}\n"
        f"Chauffeur: {payload.get('driver_id') or 'non assigne'}\n"
        f"Pickup: {payload['pickup']}\n"
        f"Dropoff: {payload['dropoff']}\n"
        f"Note: {payload.get('note') or ''}"
    )


def _result(recipient: EmergencyRecipient, status: str, *, reason: str | None = None) -> dict:
    return {
        "target": recipient.target,
        "channel": recipient.channel,
        "recipient": recipient.recipient,
        "status": status,
        "reason": reason,
    }
