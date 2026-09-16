from __future__ import annotations

from uuid import UUID

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.modules.ride.domain.entities import EmergencyContact
from app_base.modules.ride.domain.interfaces import EmergencyContactRepository


class EmergencyContactService:
    def __init__(self, contacts: EmergencyContactRepository) -> None:
        self.contacts = contacts

    async def get_for_user(self, user_id: UUID) -> dict:
        contact = await self.contacts.find_by_user_id(user_id)
        if contact is None:
            raise ApiError(404, ErrorCode.EMERGENCY_CONTACT_NOT_FOUND, "Aucun contact d'urgence configure.")
        return emergency_contact_payload(contact)

    async def upsert_for_user(
        self,
        *,
        user_id: UUID,
        contact_name: str | None,
        phone: str | None,
        email: str | None,
        relationship: str | None,
    ) -> dict:
        phone = _blank_to_none(phone)
        email = _blank_to_none(email)
        if phone is None and email is None:
            raise ApiError(
                422,
                ErrorCode.EMERGENCY_CONTACT_REQUIRED,
                "Un telephone WhatsApp ou un email est requis pour le contact d'urgence.",
                {"fields": ["phone", "email"]},
            )
        existing = await self.contacts.find_by_user_id(user_id)
        contact = existing or EmergencyContact(id=EmergencyContact.new_id(), user_id=user_id)
        contact.contact_name = _blank_to_none(contact_name)
        contact.phone = phone
        contact.email = email
        contact.relationship = _blank_to_none(relationship)
        saved = await self.contacts.save(contact)
        return emergency_contact_payload(saved)

    async def delete_for_user(self, user_id: UUID) -> dict:
        deleted = await self.contacts.delete_for_user(user_id)
        if not deleted:
            raise ApiError(404, ErrorCode.EMERGENCY_CONTACT_NOT_FOUND, "Aucun contact d'urgence configure.")
        return {"status": "deleted"}


def emergency_contact_payload(contact: EmergencyContact) -> dict:
    return {
        "id": str(contact.id),
        "user_id": str(contact.user_id),
        "contact_name": contact.contact_name,
        "phone": contact.phone,
        "email": contact.email,
        "relationship": contact.relationship,
    }


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
