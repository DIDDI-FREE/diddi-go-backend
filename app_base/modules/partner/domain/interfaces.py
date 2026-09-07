"""Partner module repository ports."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app_base.modules.partner.domain.entities import (
    Partner,
    PartnerDriverLink,
    PartnerMember,
    PartnerStatus,
    PartnerType,
    VehicleAssignment,
)


class PartnerRepository(Protocol):
    async def save(self, partner: Partner) -> Partner: ...

    async def find_by_id(self, partner_id: UUID) -> Partner | None: ...

    async def list_by(
        self,
        *,
        status: PartnerStatus | None = None,
        partner_type: PartnerType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Partner], int]: ...

    async def save_member(self, member: PartnerMember) -> PartnerMember: ...

    async def list_members(self, partner_id: UUID) -> list[PartnerMember]: ...

    async def find_active_memberships_by_user_id(self, user_id: UUID) -> list[tuple[Partner, PartnerMember]]: ...

    async def deactivate_member(self, member_id: UUID) -> bool: ...

    async def save_driver_link(self, link: PartnerDriverLink) -> PartnerDriverLink: ...

    async def find_active_driver_link(self, driver_id: UUID) -> tuple[Partner, PartnerDriverLink] | None: ...

    async def list_driver_links(self, partner_id: UUID, *, active_only: bool = True) -> list[PartnerDriverLink]: ...

    async def end_driver_link(self, partner_id: UUID, driver_id: UUID) -> bool: ...

    async def set_vehicle_partner_owner(self, vehicle_id: UUID, partner_id: UUID, driver_id: UUID) -> bool: ...

    async def save_vehicle_assignment(self, assignment: VehicleAssignment) -> VehicleAssignment: ...

    async def find_active_vehicle_assignment(self, vehicle_id: UUID) -> VehicleAssignment | None: ...

    async def end_vehicle_assignment(self, vehicle_id: UUID) -> bool: ...
