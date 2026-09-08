"""Partner use cases for DiddiGo."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.modules.partner.domain.entities import (
    Partner,
    PartnerCommissionMode,
    PartnerDriverLink,
    PartnerMember,
    PartnerMemberRole,
    PartnerStatus,
    PartnerType,
    VehicleAssignment,
)
from app_base.modules.partner.domain.interfaces import PartnerRepository
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    Vehicle,
    VehicleCategory,
    VehicleVerificationStatus,
)
from app_base.modules.ride.domain.interfaces import DriverProfileRepository, VehicleRepository


@dataclass
class PartnerService:
    partner_repo: PartnerRepository
    vehicle_repo: VehicleRepository | None = None
    driver_repo: DriverProfileRepository | None = None

    async def create_partner(
        self,
        *,
        name: str,
        partner_type: str,
        legal_name: str | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
        partner_commission_enabled: bool = False,
        partner_commission_mode: str = "percentage",
        partner_commission_rate: Decimal | str = Decimal("0.00"),
        registration_document_file_id: UUID | None = None,
        tax_document_file_id: UUID | None = None,
        representative_id_document_file_id: UUID | None = None,
        fleet_ownership_document_file_id: UUID | None = None,
        registration_document_url: str | None = None,
        tax_document_url: str | None = None,
        representative_id_document_url: str | None = None,
        fleet_ownership_document_url: str | None = None,
    ) -> dict:
        now = datetime.now(UTC)
        partner = Partner(
            id=Partner.new_id(),
            name=_required_text(name, "name"),
            partner_type=_partner_type(partner_type),
            status=PartnerStatus.PENDING_VERIFICATION,
            legal_name=_blank_to_none(legal_name),
            contact_phone=_blank_to_none(contact_phone),
            contact_email=_blank_to_none(contact_email),
            partner_commission_enabled=partner_commission_enabled,
            partner_commission_mode=_commission_mode(partner_commission_mode),
            partner_commission_rate=_commission_rate(partner_commission_rate, partner_commission_mode),
            registration_document_file_id=registration_document_file_id,
            tax_document_file_id=tax_document_file_id,
            representative_id_document_file_id=representative_id_document_file_id,
            fleet_ownership_document_file_id=fleet_ownership_document_file_id,
            registration_document_url=_blank_to_none(registration_document_url),
            tax_document_url=_blank_to_none(tax_document_url),
            representative_id_document_url=_blank_to_none(representative_id_document_url),
            fleet_ownership_document_url=_blank_to_none(fleet_ownership_document_url),
            kyc_submitted_at=now
            if _has_any_partner_kyc_document(
                registration_document_file_id=registration_document_file_id,
                tax_document_file_id=tax_document_file_id,
                representative_id_document_file_id=representative_id_document_file_id,
                fleet_ownership_document_file_id=fleet_ownership_document_file_id,
                registration_document_url=registration_document_url,
                tax_document_url=tax_document_url,
                representative_id_document_url=representative_id_document_url,
                fleet_ownership_document_url=fleet_ownership_document_url,
            )
            else None,
        )
        await self.partner_repo.save(partner)
        log_event(
            "partner.created",
            partner_id=partner.id,
            partner_type=partner.partner_type.value,
            commission_enabled=partner.partner_commission_enabled,
            commission_mode=partner.partner_commission_mode.value,
            commission_rate=partner.partner_commission_rate,
        )
        return _partner_payload(partner)

    async def list_partners(
        self,
        *,
        status: str | None = None,
        partner_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        partners, total = await self.partner_repo.list_by(
            status=_optional_status(status),
            partner_type=_optional_partner_type(partner_type),
            page=page,
            page_size=page_size,
        )
        return {
            "data": [_partner_payload(partner) for partner in partners],
            "pagination": {"page": page, "page_size": page_size, "total": total},
        }

    async def get_partner(self, partner_id: UUID) -> dict:
        partner = await self._require_partner(partner_id)
        return _partner_payload(partner)

    async def update_partner(
        self,
        partner_id: UUID,
        *,
        name: str | None = None,
        partner_type: str | None = None,
        legal_name: str | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
        partner_commission_enabled: bool | None = None,
        partner_commission_mode: str | None = None,
        partner_commission_rate: Decimal | str | None = None,
        registration_document_file_id: UUID | None = None,
        tax_document_file_id: UUID | None = None,
        representative_id_document_file_id: UUID | None = None,
        fleet_ownership_document_file_id: UUID | None = None,
        registration_document_url: str | None = None,
        tax_document_url: str | None = None,
        representative_id_document_url: str | None = None,
        fleet_ownership_document_url: str | None = None,
    ) -> dict:
        partner = await self._require_partner(partner_id)
        if name is not None:
            partner.name = _required_text(name, "name")
        if partner_type is not None:
            partner.partner_type = _partner_type(partner_type)
        if legal_name is not None:
            partner.legal_name = _blank_to_none(legal_name)
        if contact_phone is not None:
            partner.contact_phone = _blank_to_none(contact_phone)
        if contact_email is not None:
            partner.contact_email = _blank_to_none(contact_email)
        if partner_commission_enabled is not None:
            partner.partner_commission_enabled = partner_commission_enabled
        if partner_commission_mode is not None:
            partner.partner_commission_mode = _commission_mode(partner_commission_mode)
        if partner_commission_rate is not None:
            partner.partner_commission_rate = _commission_rate(
                partner_commission_rate,
                partner.partner_commission_mode.value,
            )
        _update_partner_kyc_fields(
            partner,
            registration_document_file_id=registration_document_file_id,
            tax_document_file_id=tax_document_file_id,
            representative_id_document_file_id=representative_id_document_file_id,
            fleet_ownership_document_file_id=fleet_ownership_document_file_id,
            registration_document_url=registration_document_url,
            tax_document_url=tax_document_url,
            representative_id_document_url=representative_id_document_url,
            fleet_ownership_document_url=fleet_ownership_document_url,
        )
        await self.partner_repo.save(partner)
        log_event("partner.updated", partner_id=partner.id, status=partner.status.value)
        return _partner_payload(partner)

    async def submit_kyc(
        self,
        partner_id: UUID,
        *,
        registration_document_file_id: UUID | None = None,
        tax_document_file_id: UUID | None = None,
        representative_id_document_file_id: UUID | None = None,
        fleet_ownership_document_file_id: UUID | None = None,
        registration_document_url: str | None = None,
        tax_document_url: str | None = None,
        representative_id_document_url: str | None = None,
        fleet_ownership_document_url: str | None = None,
    ) -> dict:
        partner = await self._require_partner(partner_id)
        _update_partner_kyc_fields(
            partner,
            registration_document_file_id=registration_document_file_id,
            tax_document_file_id=tax_document_file_id,
            representative_id_document_file_id=representative_id_document_file_id,
            fleet_ownership_document_file_id=fleet_ownership_document_file_id,
            registration_document_url=registration_document_url,
            tax_document_url=tax_document_url,
            representative_id_document_url=representative_id_document_url,
            fleet_ownership_document_url=fleet_ownership_document_url,
        )
        partner.status = PartnerStatus.PENDING_VERIFICATION
        partner.kyc_submitted_at = datetime.now(UTC)
        partner.kyc_reviewed_at = None
        partner.kyc_review_notes = None
        await self.partner_repo.save(partner)
        log_event("partner.kyc.submitted", partner_id=partner.id, status=partner.status.value)
        return _partner_payload(partner)

    async def activate_partner(self, partner_id: UUID) -> dict:
        partner = await self._require_partner(partner_id)
        _ensure_partner_kyc_complete(partner)
        partner.status = PartnerStatus.ACTIVE
        partner.kyc_reviewed_at = datetime.now(UTC)
        await self.partner_repo.save(partner)
        log_event("partner.activated", partner_id=partner.id)
        return _partner_payload(partner)

    async def approve_kyc(self, partner_id: UUID, *, reviewed_by_user_id: UUID, notes: str | None = None) -> dict:
        partner = await self._require_partner(partner_id)
        _ensure_partner_kyc_complete(partner)
        partner.status = PartnerStatus.ACTIVE
        partner.kyc_reviewed_at = datetime.now(UTC)
        partner.kyc_review_notes = _review_note(notes, reviewed_by_user_id)
        await self.partner_repo.save(partner)
        log_event("partner.kyc.approved", partner_id=partner.id, reviewed_by_user_id=reviewed_by_user_id)
        return _partner_payload(partner)

    async def suspend_partner(self, partner_id: UUID) -> dict:
        partner = await self._require_partner(partner_id)
        partner.status = PartnerStatus.SUSPENDED
        await self.partner_repo.save(partner)
        log_event("partner.suspended", level="warning", partner_id=partner.id)
        return _partner_payload(partner)

    async def reject_partner(self, partner_id: UUID) -> dict:
        partner = await self._require_partner(partner_id)
        partner.status = PartnerStatus.REJECTED
        partner.kyc_reviewed_at = datetime.now(UTC)
        await self.partner_repo.save(partner)
        log_event("partner.rejected", level="warning", partner_id=partner.id)
        return _partner_payload(partner)

    async def reject_kyc(self, partner_id: UUID, *, reviewed_by_user_id: UUID, notes: str | None = None) -> dict:
        partner = await self._require_partner(partner_id)
        partner.status = PartnerStatus.REJECTED
        partner.kyc_reviewed_at = datetime.now(UTC)
        partner.kyc_review_notes = _review_note(notes, reviewed_by_user_id)
        await self.partner_repo.save(partner)
        log_event(
            "partner.kyc.rejected",
            level="warning",
            partner_id=partner.id,
            reviewed_by_user_id=reviewed_by_user_id,
        )
        return _partner_payload(partner)

    async def add_member(self, partner_id: UUID, *, user_id: UUID, role: str) -> dict:
        await self._require_partner(partner_id)
        member = PartnerMember(
            id=PartnerMember.new_id(),
            partner_id=partner_id,
            user_id=user_id,
            role=_member_role(role),
            active=True,
        )
        try:
            await self.partner_repo.save_member(member)
        except Exception as exc:
            if "partner_members_partner_user_unique" in str(exc):
                raise ApiError(
                    409,
                    ErrorCode.PARTNER_ALREADY_EXISTS,
                    "Cet utilisateur est deja membre de ce partenaire.",
                ) from exc
            raise
        log_event("partner.member.added", partner_id=partner_id, user_id=user_id, role=member.role.value)
        return _member_payload(member)

    async def list_members(self, partner_id: UUID) -> dict:
        await self._require_partner(partner_id)
        members = await self.partner_repo.list_members(partner_id)
        return {"data": [_member_payload(member) for member in members]}

    async def deactivate_member(self, partner_id: UUID, member_id: UUID) -> dict:
        await self._require_partner(partner_id)
        removed = await self.partner_repo.deactivate_member(member_id)
        if not removed:
            raise ApiError(404, ErrorCode.PARTNER_MEMBER_NOT_FOUND, "Membre partenaire introuvable.")
        log_event("partner.member.deactivated", partner_id=partner_id, member_id=member_id)
        return {"status": "deactivated", "member_id": str(member_id)}

    async def get_my_partners(self, user_id: UUID) -> dict:
        rows = await self.partner_repo.find_active_memberships_by_user_id(user_id)
        return {
            "partners": [
                {
                    **_partner_payload(partner),
                    "role": member.role.value,
                    "membership_id": str(member.id),
                }
                for partner, member in rows
            ]
        }

    async def affiliate_driver(self, partner_id: UUID, *, driver_id: UUID) -> dict:
        partner = await self._require_active_partner(partner_id)
        existing = await self.partner_repo.find_active_driver_link(driver_id)
        if existing is not None:
            existing_partner, _link = existing
            raise ApiError(
                409,
                ErrorCode.DRIVER_ALREADY_AFFILIATED,
                "Ce chauffeur est deja affilie a un partenaire actif.",
                {"partner_id": str(existing_partner.id)},
            )
        link = PartnerDriverLink(id=PartnerDriverLink.new_id(), partner_id=partner.id, driver_id=driver_id)
        await self.partner_repo.save_driver_link(link)
        log_event("partner.driver.affiliated", partner_id=partner.id, driver_id=driver_id)
        return _driver_link_payload(link)

    async def list_drivers(self, partner_id: UUID) -> dict:
        await self._require_partner(partner_id)
        links = await self.partner_repo.list_driver_links(partner_id)
        return {"data": [_driver_link_payload(link) for link in links]}

    async def unaffiliate_driver(self, partner_id: UUID, driver_id: UUID) -> dict:
        await self._require_partner(partner_id)
        removed = await self.partner_repo.end_driver_link(partner_id, driver_id)
        if not removed:
            raise ApiError(404, ErrorCode.DRIVER_NOT_AFFILIATED, "Ce chauffeur n'est pas affilie a ce partenaire.")
        log_event("partner.driver.unaffiliated", partner_id=partner_id, driver_id=driver_id)
        return {"status": "ended", "partner_id": str(partner_id), "driver_id": str(driver_id)}

    async def assign_vehicle(self, partner_id: UUID, *, vehicle_id: UUID, driver_id: UUID) -> dict:
        await self._require_active_partner(partner_id)
        driver_link = await self.partner_repo.find_active_driver_link(driver_id)
        if driver_link is None or driver_link[0].id != partner_id:
            raise ApiError(
                409,
                ErrorCode.DRIVER_NOT_AFFILIATED,
                "Le chauffeur doit etre affilie au partenaire avant assignation du vehicule.",
            )
        current = await self.partner_repo.find_active_vehicle_assignment(vehicle_id)
        if current is not None:
            raise ApiError(
                409,
                ErrorCode.VEHICLE_ALREADY_ASSIGNED,
                "Ce vehicule est deja assigne a un chauffeur actif.",
                {"driver_id": str(current.driver_id)},
            )
        if not await self.partner_repo.set_vehicle_partner_owner(vehicle_id, partner_id, driver_id):
            raise ApiError(404, ErrorCode.VEHICLE_NOT_FOUND, "Vehicule introuvable.")
        assignment = VehicleAssignment(
            id=VehicleAssignment.new_id(),
            partner_id=partner_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
        )
        await self.partner_repo.save_vehicle_assignment(assignment)
        log_event("partner.vehicle.assigned", partner_id=partner_id, vehicle_id=vehicle_id, driver_id=driver_id)
        return _vehicle_assignment_payload(assignment)

    async def create_vehicle(
        self,
        partner_id: UUID,
        *,
        driver_id: UUID,
        plate_number: str,
        make: str | None = None,
        model: str | None = None,
        color: str | None = None,
        category: str = "standard",
        comfort_level: str = "standard",
        registration_document_file_id: UUID | None = None,
        insurance_document_file_id: UUID | None = None,
        technical_inspection_document_file_id: UUID | None = None,
        transport_authorization_document_file_id: UUID | None = None,
        vehicle_photo_file_id: UUID | None = None,
        vehicle_front_photo_file_id: UUID | None = None,
        vehicle_back_photo_file_id: UUID | None = None,
        vehicle_left_photo_file_id: UUID | None = None,
        vehicle_right_photo_file_id: UUID | None = None,
        vehicle_interior_photo_file_id: UUID | None = None,
        registration_document_url: str | None = None,
        insurance_document_url: str | None = None,
        technical_inspection_document_url: str | None = None,
        transport_authorization_document_url: str | None = None,
        vehicle_photo_url: str | None = None,
        vehicle_front_photo_url: str | None = None,
        vehicle_back_photo_url: str | None = None,
        vehicle_left_photo_url: str | None = None,
        vehicle_right_photo_url: str | None = None,
        vehicle_interior_photo_url: str | None = None,
    ) -> dict:
        if self.vehicle_repo is None or self.driver_repo is None:
            raise ApiError(
                500,
                ErrorCode.PARTNER_VEHICLE_REPOSITORY_MISSING,
                "Creation vehicule partenaire non configuree.",
            )
        await self._require_active_partner(partner_id)
        if await self.driver_repo.find_by_id(driver_id) is None:
            raise ApiError(404, ErrorCode.DRIVER_PROFILE_NOT_FOUND, "Profil chauffeur introuvable.")
        await self._ensure_driver_affiliated_to_partner(partner_id, driver_id)
        vehicle = Vehicle(
            id=Vehicle.new_id(),
            driver_id=driver_id,
            plate_number=_required_text(plate_number, "plate_number").upper(),
            make=_blank_to_none(make),
            model=_blank_to_none(model),
            color=_blank_to_none(color),
            registration_document_file_id=registration_document_file_id,
            insurance_document_file_id=insurance_document_file_id,
            technical_inspection_document_file_id=technical_inspection_document_file_id,
            transport_authorization_document_file_id=transport_authorization_document_file_id,
            vehicle_photo_file_id=vehicle_photo_file_id,
            vehicle_front_photo_file_id=vehicle_front_photo_file_id,
            vehicle_back_photo_file_id=vehicle_back_photo_file_id,
            vehicle_left_photo_file_id=vehicle_left_photo_file_id,
            vehicle_right_photo_file_id=vehicle_right_photo_file_id,
            vehicle_interior_photo_file_id=vehicle_interior_photo_file_id,
            registration_document_url=_blank_to_none(registration_document_url),
            insurance_document_url=_blank_to_none(insurance_document_url),
            technical_inspection_document_url=_blank_to_none(technical_inspection_document_url),
            transport_authorization_document_url=_blank_to_none(transport_authorization_document_url),
            vehicle_photo_url=_blank_to_none(vehicle_photo_url),
            vehicle_front_photo_url=_blank_to_none(vehicle_front_photo_url),
            vehicle_back_photo_url=_blank_to_none(vehicle_back_photo_url),
            vehicle_left_photo_url=_blank_to_none(vehicle_left_photo_url),
            vehicle_right_photo_url=_blank_to_none(vehicle_right_photo_url),
            vehicle_interior_photo_url=_blank_to_none(vehicle_interior_photo_url),
            verification_status=VehicleVerificationStatus.PENDING_VERIFICATION,
            owner_type="partner",
            partner_id=partner_id,
            category=_vehicle_category(category),
            comfort_level=_comfort_level(comfort_level),
            active=True,
            created_at=datetime.now(UTC),
        )
        try:
            await self.vehicle_repo.save(vehicle)
        except Exception as exc:
            if "plate_number" in str(exc):
                raise ApiError(409, ErrorCode.PLATE_ALREADY_REGISTERED, "Cette plaque est deja enregistree.") from exc
            raise
        assignment = VehicleAssignment(
            id=VehicleAssignment.new_id(),
            partner_id=partner_id,
            vehicle_id=vehicle.id,
            driver_id=driver_id,
        )
        await self.partner_repo.save_vehicle_assignment(assignment)
        log_event(
            "partner.vehicle.created",
            partner_id=partner_id,
            vehicle_id=vehicle.id,
            driver_id=driver_id,
            category=vehicle.category.value,
            comfort_level=vehicle.comfort_level.value,
            verification_status=vehicle.verification_status.value,
        )
        return {"vehicle": _vehicle_payload(vehicle), "assignment": _vehicle_assignment_payload(assignment)}

    async def unassign_vehicle(self, partner_id: UUID, vehicle_id: UUID) -> dict:
        await self._require_partner(partner_id)
        removed = await self.partner_repo.end_vehicle_assignment(vehicle_id)
        if not removed:
            raise ApiError(404, ErrorCode.VEHICLE_ASSIGNMENT_NOT_FOUND, "Assignation vehicule introuvable.")
        log_event("partner.vehicle.unassigned", partner_id=partner_id, vehicle_id=vehicle_id)
        return {"status": "ended", "partner_id": str(partner_id), "vehicle_id": str(vehicle_id)}

    async def driver_is_blocked_by_partner(self, driver_id: UUID) -> tuple[bool, str | None]:
        link = await self.partner_repo.find_active_driver_link(driver_id)
        if link is None:
            return False, None
        partner, _driver_link = link
        if partner.status != PartnerStatus.ACTIVE:
            return True, f"partner_not_active:{partner.status.value}"
        return False, None

    async def _require_partner(self, partner_id: UUID) -> Partner:
        partner = await self.partner_repo.find_by_id(partner_id)
        if partner is None:
            raise ApiError(404, ErrorCode.PARTNER_NOT_FOUND, "Partenaire introuvable.")
        return partner

    async def _require_active_partner(self, partner_id: UUID) -> Partner:
        partner = await self._require_partner(partner_id)
        if partner.status != PartnerStatus.ACTIVE:
            raise ApiError(
                409,
                ErrorCode.PARTNER_NOT_ACTIVE,
                "Le partenaire doit etre actif pour cette operation.",
                {"status": partner.status.value},
            )
        return partner

    async def _ensure_driver_affiliated_to_partner(self, partner_id: UUID, driver_id: UUID) -> None:
        driver_link = await self.partner_repo.find_active_driver_link(driver_id)
        if driver_link is not None:
            existing_partner, _link = driver_link
            if existing_partner.id != partner_id:
                raise ApiError(
                    409,
                    ErrorCode.DRIVER_ALREADY_AFFILIATED,
                    "Ce chauffeur est deja affilie a un autre partenaire actif.",
                    {"partner_id": str(existing_partner.id)},
                )
            return
        await self.partner_repo.save_driver_link(
            PartnerDriverLink(id=PartnerDriverLink.new_id(), partner_id=partner_id, driver_id=driver_id)
        )
        log_event("partner.driver.affiliated", partner_id=partner_id, driver_id=driver_id, source="vehicle_creation")


def _partner_payload(partner: Partner) -> dict:
    return {
        "id": str(partner.id),
        "name": partner.name,
        "partner_type": partner.partner_type.value,
        "status": partner.status.value,
        "legal_name": partner.legal_name,
        "contact_phone": partner.contact_phone,
        "contact_email": partner.contact_email,
        "partner_commission_enabled": partner.partner_commission_enabled,
        "partner_commission_mode": partner.partner_commission_mode.value,
        "partner_commission_rate": float(partner.partner_commission_rate),
        "kyc": {
            "registration_document_file_id": str(partner.registration_document_file_id)
            if partner.registration_document_file_id
            else None,
            "tax_document_file_id": str(partner.tax_document_file_id) if partner.tax_document_file_id else None,
            "representative_id_document_file_id": str(partner.representative_id_document_file_id)
            if partner.representative_id_document_file_id
            else None,
            "fleet_ownership_document_file_id": str(partner.fleet_ownership_document_file_id)
            if partner.fleet_ownership_document_file_id
            else None,
            "registration_document_url": partner.registration_document_url,
            "tax_document_url": partner.tax_document_url,
            "representative_id_document_url": partner.representative_id_document_url,
            "fleet_ownership_document_url": partner.fleet_ownership_document_url,
            "submitted_at": partner.kyc_submitted_at.isoformat() if partner.kyc_submitted_at else None,
            "reviewed_at": partner.kyc_reviewed_at.isoformat() if partner.kyc_reviewed_at else None,
            "review_notes": partner.kyc_review_notes,
        },
        "created_at": partner.created_at.isoformat() if partner.created_at else None,
        "updated_at": partner.updated_at.isoformat() if partner.updated_at else None,
    }


def _member_payload(member: PartnerMember) -> dict:
    return {
        "id": str(member.id),
        "partner_id": str(member.partner_id),
        "user_id": str(member.user_id),
        "role": member.role.value,
        "active": member.active,
        "created_at": member.created_at.isoformat() if member.created_at else None,
        "updated_at": member.updated_at.isoformat() if member.updated_at else None,
    }


def _driver_link_payload(link: PartnerDriverLink) -> dict:
    return {
        "id": str(link.id),
        "partner_id": str(link.partner_id),
        "driver_id": str(link.driver_id),
        "active": link.active,
        "created_at": link.created_at.isoformat() if link.created_at else None,
        "ended_at": link.ended_at.isoformat() if link.ended_at else None,
    }


def _vehicle_assignment_payload(assignment: VehicleAssignment) -> dict:
    return {
        "id": str(assignment.id),
        "partner_id": str(assignment.partner_id),
        "vehicle_id": str(assignment.vehicle_id),
        "driver_id": str(assignment.driver_id),
        "active": assignment.active,
        "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
        "ended_at": assignment.ended_at.isoformat() if assignment.ended_at else None,
    }


def _vehicle_payload(vehicle: Vehicle) -> dict:
    return {
        "id": str(vehicle.id),
        "driver_id": str(vehicle.driver_id),
        "plate_number": vehicle.plate_number,
        "make": vehicle.make,
        "model": vehicle.model,
        "color": vehicle.color,
        "category": vehicle.category.value,
        "comfort_level": vehicle.comfort_level.value,
        "registration_document_file_id": str(vehicle.registration_document_file_id)
        if vehicle.registration_document_file_id
        else None,
        "insurance_document_file_id": str(vehicle.insurance_document_file_id)
        if vehicle.insurance_document_file_id
        else None,
        "technical_inspection_document_file_id": str(vehicle.technical_inspection_document_file_id)
        if vehicle.technical_inspection_document_file_id
        else None,
        "transport_authorization_document_file_id": str(vehicle.transport_authorization_document_file_id)
        if vehicle.transport_authorization_document_file_id
        else None,
        "vehicle_photo_file_id": str(vehicle.vehicle_photo_file_id) if vehicle.vehicle_photo_file_id else None,
        "vehicle_front_photo_file_id": str(vehicle.vehicle_front_photo_file_id)
        if vehicle.vehicle_front_photo_file_id
        else None,
        "vehicle_back_photo_file_id": str(vehicle.vehicle_back_photo_file_id)
        if vehicle.vehicle_back_photo_file_id
        else None,
        "vehicle_left_photo_file_id": str(vehicle.vehicle_left_photo_file_id)
        if vehicle.vehicle_left_photo_file_id
        else None,
        "vehicle_right_photo_file_id": str(vehicle.vehicle_right_photo_file_id)
        if vehicle.vehicle_right_photo_file_id
        else None,
        "vehicle_interior_photo_file_id": str(vehicle.vehicle_interior_photo_file_id)
        if vehicle.vehicle_interior_photo_file_id
        else None,
        "registration_document_url": vehicle.registration_document_url,
        "insurance_document_url": vehicle.insurance_document_url,
        "technical_inspection_document_url": vehicle.technical_inspection_document_url,
        "transport_authorization_document_url": vehicle.transport_authorization_document_url,
        "vehicle_photo_url": vehicle.vehicle_photo_url,
        "vehicle_front_photo_url": vehicle.vehicle_front_photo_url,
        "vehicle_back_photo_url": vehicle.vehicle_back_photo_url,
        "vehicle_left_photo_url": vehicle.vehicle_left_photo_url,
        "vehicle_right_photo_url": vehicle.vehicle_right_photo_url,
        "vehicle_interior_photo_url": vehicle.vehicle_interior_photo_url,
        "verification_status": vehicle.verification_status.value,
        "verified_at": vehicle.verified_at.isoformat() if vehicle.verified_at else None,
        "reviewed_at": vehicle.reviewed_at.isoformat() if vehicle.reviewed_at else None,
        "review_notes": vehicle.review_notes,
        "owner_type": vehicle.owner_type,
        "partner_id": str(vehicle.partner_id) if vehicle.partner_id else None,
        "active": vehicle.active,
        "created_at": vehicle.created_at.isoformat() if vehicle.created_at else None,
    }


def _partner_type(value: str) -> PartnerType:
    try:
        return PartnerType(value)
    except ValueError as exc:
        raise ApiError(
            422,
            ErrorCode.INVALID_PARTNER_TYPE,
            "Type partenaire invalide.",
            {"field": "partner_type", "allowed": [item.value for item in PartnerType]},
        ) from exc


def _optional_partner_type(value: str | None) -> PartnerType | None:
    return _partner_type(value) if value else None


def _optional_status(value: str | None) -> PartnerStatus | None:
    if not value:
        return None
    try:
        return PartnerStatus(value)
    except ValueError as exc:
        raise ApiError(
            422,
            ErrorCode.INVALID_PARTNER_STATUS,
            "Statut partenaire invalide.",
            {"field": "status", "allowed": [item.value for item in PartnerStatus]},
        ) from exc


def _member_role(value: str) -> PartnerMemberRole:
    try:
        return PartnerMemberRole(value)
    except ValueError as exc:
        raise ApiError(
            422,
            ErrorCode.INVALID_PARTNER_ROLE,
            "Role partenaire invalide.",
            {"field": "role", "allowed": [item.value for item in PartnerMemberRole]},
        ) from exc


def _vehicle_category(value: str) -> VehicleCategory:
    try:
        return VehicleCategory(value)
    except ValueError as exc:
        raise ApiError(
            422,
            ErrorCode.INVALID_VEHICLE_CATEGORY,
            "Categorie de vehicule invalide.",
            {"field": "category", "allowed": [item.value for item in VehicleCategory]},
        ) from exc


def _comfort_level(value: str) -> ComfortLevel:
    try:
        return ComfortLevel(value)
    except ValueError as exc:
        raise ApiError(
            422,
            ErrorCode.INVALID_COMFORT_LEVEL,
            "Niveau de confort invalide.",
            {"field": "comfort_level", "allowed": [item.value for item in ComfortLevel]},
        ) from exc


def _commission_mode(value: str) -> PartnerCommissionMode:
    try:
        return PartnerCommissionMode(value)
    except ValueError as exc:
        raise ApiError(
            422,
            ErrorCode.INVALID_PARTNER_COMMISSION,
            "Mode de commission partenaire invalide.",
            {"field": "partner_commission_mode", "allowed": [item.value for item in PartnerCommissionMode]},
        ) from exc


def _commission_rate(value: Decimal | str, mode: str) -> Decimal:
    try:
        rate = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ApiError(
            422,
            ErrorCode.INVALID_PARTNER_COMMISSION,
            "Commission partenaire invalide.",
            {"field": "partner_commission_rate"},
        ) from exc
    if rate < Decimal("0"):
        raise ApiError(
            422,
            ErrorCode.INVALID_PARTNER_COMMISSION,
            "Commission partenaire invalide.",
            {"field": "partner_commission_rate", "reason": "negative"},
        )
    if mode == PartnerCommissionMode.PERCENTAGE.value and rate > Decimal("1"):
        raise ApiError(
            422,
            ErrorCode.INVALID_PARTNER_COMMISSION,
            "Commission partenaire en pourcentage invalide.",
            {"field": "partner_commission_rate", "max": "1.00"},
        )
    return rate


def _update_partner_kyc_fields(
    partner: Partner,
    *,
    registration_document_file_id: UUID | None,
    tax_document_file_id: UUID | None,
    representative_id_document_file_id: UUID | None,
    fleet_ownership_document_file_id: UUID | None,
    registration_document_url: str | None,
    tax_document_url: str | None,
    representative_id_document_url: str | None,
    fleet_ownership_document_url: str | None,
) -> None:
    if registration_document_file_id is not None:
        partner.registration_document_file_id = registration_document_file_id
    if tax_document_file_id is not None:
        partner.tax_document_file_id = tax_document_file_id
    if representative_id_document_file_id is not None:
        partner.representative_id_document_file_id = representative_id_document_file_id
    if fleet_ownership_document_file_id is not None:
        partner.fleet_ownership_document_file_id = fleet_ownership_document_file_id
    if registration_document_url is not None:
        partner.registration_document_url = _blank_to_none(registration_document_url)
    if tax_document_url is not None:
        partner.tax_document_url = _blank_to_none(tax_document_url)
    if representative_id_document_url is not None:
        partner.representative_id_document_url = _blank_to_none(representative_id_document_url)
    if fleet_ownership_document_url is not None:
        partner.fleet_ownership_document_url = _blank_to_none(fleet_ownership_document_url)


def _ensure_partner_kyc_complete(partner: Partner) -> None:
    missing = [
        key
        for key, present in {
            "registration_document": bool(partner.registration_document_file_id or partner.registration_document_url),
            "tax_document": bool(partner.tax_document_file_id or partner.tax_document_url),
            "representative_id_document": bool(
                partner.representative_id_document_file_id or partner.representative_id_document_url
            ),
        }.items()
        if not present
    ]
    if missing:
        raise ApiError(
            422,
            ErrorCode.INVALID_PARTNER_KYC_DOCUMENTS,
            "Le dossier KYC partenaire est incomplet.",
            {"missing_documents": missing},
        )


def _has_any_partner_kyc_document(**values: object) -> bool:
    return any(value is not None and str(value).strip() for value in values.values())


def _required_text(value: str, field: str) -> str:
    cleaned = _blank_to_none(value)
    if cleaned is None:
        raise ApiError(422, "VALIDATION_ERROR", "Champ obligatoire.", {"field": field})
    return cleaned


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _review_note(notes: str | None, reviewed_by_user_id: UUID) -> str:
    cleaned = _blank_to_none(notes)
    suffix = f"reviewed_by={reviewed_by_user_id}"
    return f"{cleaned} ({suffix})" if cleaned else suffix
