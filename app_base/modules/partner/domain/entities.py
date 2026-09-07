"""Partner domain entities.

The partner module owns the local DiddiGo business roles for fleets and
companies. DiddiFreeID remains responsible for global authentication only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class PartnerType(str, Enum):
    COMPANY = "company"
    FLEET_OWNER = "fleet_owner"


class PartnerStatus(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class PartnerMemberRole(str, Enum):
    MANAGER = "partner_manager"
    OPERATOR = "partner_operator"
    VIEWER = "partner_viewer"


class PartnerCommissionMode(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class VehicleOwnerType(str, Enum):
    DRIVER = "driver"
    PARTNER = "partner"


@dataclass
class Partner:
    id: UUID
    name: str
    partner_type: PartnerType
    status: PartnerStatus = PartnerStatus.PENDING_VERIFICATION
    legal_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    partner_commission_enabled: bool = False
    partner_commission_mode: PartnerCommissionMode = PartnerCommissionMode.PERCENTAGE
    partner_commission_rate: Decimal = Decimal("0.00")
    registration_document_file_id: UUID | None = None
    tax_document_file_id: UUID | None = None
    representative_id_document_file_id: UUID | None = None
    fleet_ownership_document_file_id: UUID | None = None
    registration_document_url: str | None = None
    tax_document_url: str | None = None
    representative_id_document_url: str | None = None
    fleet_ownership_document_url: str | None = None
    kyc_submitted_at: datetime | None = None
    kyc_reviewed_at: datetime | None = None
    kyc_review_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class PartnerMember:
    id: UUID
    partner_id: UUID
    user_id: UUID
    role: PartnerMemberRole
    active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class PartnerDriverLink:
    id: UUID
    partner_id: UUID
    driver_id: UUID
    active: bool = True
    created_at: datetime | None = None
    ended_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()


@dataclass
class VehicleAssignment:
    id: UUID
    partner_id: UUID
    vehicle_id: UUID
    driver_id: UUID
    active: bool = True
    created_at: datetime | None = None
    ended_at: datetime | None = None

    @staticmethod
    def new_id() -> UUID:
        return uuid4()
