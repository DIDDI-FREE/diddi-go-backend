"""SQLAlchemy-backed partner repositories."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

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
from app_base.modules.partner.infra import models as orm
from app_base.modules.ride.infra.models import VehicleModel


class SqlAlchemyPartnerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, partner: Partner) -> Partner:
        row: orm.PartnerModel | None = await self._session.get(orm.PartnerModel, partner.id)
        if row is None:
            row = orm.PartnerModel(id=partner.id)
            self._session.add(row)
        row.name = partner.name
        row.partner_type = partner.partner_type.value
        row.status = partner.status.value
        row.legal_name = partner.legal_name
        row.contact_phone = partner.contact_phone
        row.contact_email = partner.contact_email
        row.partner_commission_enabled = partner.partner_commission_enabled
        row.partner_commission_mode = partner.partner_commission_mode.value
        row.partner_commission_rate = partner.partner_commission_rate
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        partner.created_at = row.created_at
        partner.updated_at = row.updated_at
        return partner

    async def find_by_id(self, partner_id: UUID) -> Partner | None:
        row = await self._session.get(orm.PartnerModel, partner_id)
        if row is None:
            return None
        return _partner_to_domain(row)

    async def list_by(
        self,
        *,
        status: PartnerStatus | None = None,
        partner_type: PartnerType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Partner], int]:
        q = select(orm.PartnerModel)
        if status is not None:
            q = q.where(orm.PartnerModel.status == status.value)
        if partner_type is not None:
            q = q.where(orm.PartnerModel.partner_type == partner_type.value)
        total = (await self._session.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
        q = q.order_by(orm.PartnerModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self._session.execute(q)
        return [_partner_to_domain(row) for row in result.scalars().all()], int(total)

    async def save_member(self, member: PartnerMember) -> PartnerMember:
        row: orm.PartnerMemberModel | None = await self._session.get(orm.PartnerMemberModel, member.id)
        if row is None:
            row = orm.PartnerMemberModel(id=member.id)
            self._session.add(row)
        row.partner_id = member.partner_id
        row.user_id = member.user_id
        row.role = member.role.value
        row.active = member.active
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        member.created_at = row.created_at
        member.updated_at = row.updated_at
        return member

    async def list_members(self, partner_id: UUID) -> list[PartnerMember]:
        result = await self._session.execute(
            select(orm.PartnerMemberModel)
            .where(orm.PartnerMemberModel.partner_id == partner_id)
            .order_by(orm.PartnerMemberModel.created_at.asc()),
        )
        return [_member_to_domain(row) for row in result.scalars().all()]

    async def find_active_memberships_by_user_id(self, user_id: UUID) -> list[tuple[Partner, PartnerMember]]:
        result = await self._session.execute(
            select(orm.PartnerModel, orm.PartnerMemberModel)
            .join(orm.PartnerMemberModel, orm.PartnerMemberModel.partner_id == orm.PartnerModel.id)
            .where(orm.PartnerMemberModel.user_id == user_id, orm.PartnerMemberModel.active.is_(True))
            .order_by(orm.PartnerModel.created_at.desc()),
        )
        return [(_partner_to_domain(partner), _member_to_domain(member)) for partner, member in result.all()]

    async def deactivate_member(self, member_id: UUID) -> bool:
        row = await self._session.get(orm.PartnerMemberModel, member_id)
        if row is None:
            return False
        row.active = False
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def save_driver_link(self, link: PartnerDriverLink) -> PartnerDriverLink:
        row: orm.PartnerDriverLinkModel | None = await self._session.get(orm.PartnerDriverLinkModel, link.id)
        if row is None:
            row = orm.PartnerDriverLinkModel(id=link.id)
            self._session.add(row)
        row.partner_id = link.partner_id
        row.driver_id = link.driver_id
        row.active = link.active
        row.ended_at = link.ended_at
        await self._session.flush()
        link.created_at = row.created_at
        return link

    async def find_active_driver_link(self, driver_id: UUID) -> tuple[Partner, PartnerDriverLink] | None:
        result = await self._session.execute(
            select(orm.PartnerModel, orm.PartnerDriverLinkModel)
            .join(orm.PartnerDriverLinkModel, orm.PartnerDriverLinkModel.partner_id == orm.PartnerModel.id)
            .where(
                orm.PartnerDriverLinkModel.driver_id == driver_id,
                orm.PartnerDriverLinkModel.active.is_(True),
            )
            .limit(1),
        )
        row = result.one_or_none()
        if row is None:
            return None
        partner, link = row
        return _partner_to_domain(partner), _driver_link_to_domain(link)

    async def list_driver_links(self, partner_id: UUID, *, active_only: bool = True) -> list[PartnerDriverLink]:
        q = select(orm.PartnerDriverLinkModel).where(orm.PartnerDriverLinkModel.partner_id == partner_id)
        if active_only:
            q = q.where(orm.PartnerDriverLinkModel.active.is_(True))
        q = q.order_by(orm.PartnerDriverLinkModel.created_at.desc())
        result = await self._session.execute(q)
        return [_driver_link_to_domain(row) for row in result.scalars().all()]

    async def end_driver_link(self, partner_id: UUID, driver_id: UUID) -> bool:
        result = await self._session.execute(
            update(orm.PartnerDriverLinkModel)
            .where(
                orm.PartnerDriverLinkModel.partner_id == partner_id,
                orm.PartnerDriverLinkModel.driver_id == driver_id,
                orm.PartnerDriverLinkModel.active.is_(True),
            )
            .values(active=False, ended_at=datetime.now(UTC)),
        )
        await self._session.flush()
        return result.rowcount > 0

    async def set_vehicle_partner_owner(self, vehicle_id: UUID, partner_id: UUID, driver_id: UUID) -> bool:
        row = await self._session.get(VehicleModel, vehicle_id)
        if row is None:
            return False
        row.owner_type = "partner"
        row.partner_id = partner_id
        row.driver_id = driver_id
        await self._session.flush()
        return True

    async def save_vehicle_assignment(self, assignment: VehicleAssignment) -> VehicleAssignment:
        row: orm.VehicleAssignmentModel | None = await self._session.get(orm.VehicleAssignmentModel, assignment.id)
        if row is None:
            row = orm.VehicleAssignmentModel(id=assignment.id)
            self._session.add(row)
        row.partner_id = assignment.partner_id
        row.vehicle_id = assignment.vehicle_id
        row.driver_id = assignment.driver_id
        row.active = assignment.active
        row.ended_at = assignment.ended_at
        await self._session.flush()
        assignment.created_at = row.created_at
        return assignment

    async def find_active_vehicle_assignment(self, vehicle_id: UUID) -> VehicleAssignment | None:
        result = await self._session.execute(
            select(orm.VehicleAssignmentModel)
            .where(
                orm.VehicleAssignmentModel.vehicle_id == vehicle_id,
                orm.VehicleAssignmentModel.active.is_(True),
            )
            .limit(1),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _vehicle_assignment_to_domain(row)

    async def end_vehicle_assignment(self, vehicle_id: UUID) -> bool:
        result = await self._session.execute(
            update(orm.VehicleAssignmentModel)
            .where(
                orm.VehicleAssignmentModel.vehicle_id == vehicle_id,
                orm.VehicleAssignmentModel.active.is_(True),
            )
            .values(active=False, ended_at=datetime.now(UTC)),
        )
        await self._session.flush()
        return result.rowcount > 0


def _partner_to_domain(row: orm.PartnerModel) -> Partner:
    return Partner(
        id=row.id,
        name=row.name,
        partner_type=PartnerType(row.partner_type),
        status=PartnerStatus(row.status),
        legal_name=row.legal_name,
        contact_phone=row.contact_phone,
        contact_email=row.contact_email,
        partner_commission_enabled=row.partner_commission_enabled,
        partner_commission_mode=PartnerCommissionMode(row.partner_commission_mode),
        partner_commission_rate=Decimal(str(row.partner_commission_rate)),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _member_to_domain(row: orm.PartnerMemberModel) -> PartnerMember:
    return PartnerMember(
        id=row.id,
        partner_id=row.partner_id,
        user_id=row.user_id,
        role=PartnerMemberRole(row.role),
        active=row.active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _driver_link_to_domain(row: orm.PartnerDriverLinkModel) -> PartnerDriverLink:
    return PartnerDriverLink(
        id=row.id,
        partner_id=row.partner_id,
        driver_id=row.driver_id,
        active=row.active,
        created_at=row.created_at,
        ended_at=row.ended_at,
    )


def _vehicle_assignment_to_domain(row: orm.VehicleAssignmentModel) -> VehicleAssignment:
    return VehicleAssignment(
        id=row.id,
        partner_id=row.partner_id,
        vehicle_id=row.vehicle_id,
        driver_id=row.driver_id,
        active=row.active,
        created_at=row.created_at,
        ended_at=row.ended_at,
    )
