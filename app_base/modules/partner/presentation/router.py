"""Partner API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app_base.core.auth_deps import get_current_active_user, require_role
from app_base.core.deps import partner_service
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.partner.application.services import PartnerService
from app_base.modules.partner.presentation.schemas import (
    PartnerCreateRequest,
    PartnerDriverAffiliateRequest,
    PartnerKycReviewRequest,
    PartnerKycSubmitRequest,
    PartnerMemberCreateRequest,
    PartnerUpdateRequest,
    PartnerVehicleAssignRequest,
)

admin_router = APIRouter(prefix="/admin/partners", tags=["admin-partners"])
router = APIRouter(prefix="/partners", tags=["partners"])


@admin_router.post("", status_code=201)
async def create_partner(
    payload: PartnerCreateRequest,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.create_partner(**payload.model_dump())


@admin_router.get("")
async def list_partners(
    status: str | None = None,
    partner_type: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.list_partners(status=status, partner_type=partner_type, page=page, page_size=page_size)


@admin_router.get("/{partner_id}")
async def get_partner(
    partner_id: UUID,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.get_partner(partner_id)


@admin_router.patch("/{partner_id}")
async def update_partner(
    partner_id: UUID,
    payload: PartnerUpdateRequest,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.update_partner(partner_id, **payload.model_dump(exclude_unset=True))


@admin_router.post("/{partner_id}/activate")
async def activate_partner(
    partner_id: UUID,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.activate_partner(partner_id)


@admin_router.patch("/{partner_id}/kyc")
async def submit_partner_kyc(
    partner_id: UUID,
    payload: PartnerKycSubmitRequest,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.submit_kyc(partner_id, **payload.model_dump(exclude_unset=True))


@admin_router.post("/{partner_id}/kyc/approve")
async def approve_partner_kyc(
    partner_id: UUID,
    payload: PartnerKycReviewRequest,
    service: PartnerService = Depends(partner_service),
    current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.approve_kyc(partner_id, reviewed_by_user_id=current_user.id, notes=payload.notes)


@admin_router.post("/{partner_id}/kyc/reject")
async def reject_partner_kyc(
    partner_id: UUID,
    payload: PartnerKycReviewRequest,
    service: PartnerService = Depends(partner_service),
    current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.reject_kyc(partner_id, reviewed_by_user_id=current_user.id, notes=payload.notes)


@admin_router.post("/{partner_id}/suspend")
async def suspend_partner(
    partner_id: UUID,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.suspend_partner(partner_id)


@admin_router.post("/{partner_id}/reject")
async def reject_partner(
    partner_id: UUID,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.reject_partner(partner_id)


@admin_router.post("/{partner_id}/members", status_code=201)
async def add_member(
    partner_id: UUID,
    payload: PartnerMemberCreateRequest,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.add_member(partner_id, user_id=payload.user_id, role=payload.role)


@admin_router.get("/{partner_id}/members")
async def list_members(
    partner_id: UUID,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.list_members(partner_id)


@admin_router.delete("/{partner_id}/members/{member_id}")
async def deactivate_member(
    partner_id: UUID,
    member_id: UUID,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.deactivate_member(partner_id, member_id)


@admin_router.post("/{partner_id}/drivers", status_code=201)
async def affiliate_driver(
    partner_id: UUID,
    payload: PartnerDriverAffiliateRequest,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.affiliate_driver(partner_id, driver_id=payload.driver_id)


@admin_router.get("/{partner_id}/drivers")
async def list_drivers(
    partner_id: UUID,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.list_drivers(partner_id)


@admin_router.delete("/{partner_id}/drivers/{driver_id}")
async def unaffiliate_driver(
    partner_id: UUID,
    driver_id: UUID,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.unaffiliate_driver(partner_id, driver_id)


@admin_router.post("/{partner_id}/vehicles/{vehicle_id}/assign", status_code=201)
async def assign_vehicle(
    partner_id: UUID,
    vehicle_id: UUID,
    payload: PartnerVehicleAssignRequest,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.assign_vehicle(partner_id, vehicle_id=vehicle_id, driver_id=payload.driver_id)


@admin_router.post("/{partner_id}/vehicles/{vehicle_id}/unassign")
async def unassign_vehicle(
    partner_id: UUID,
    vehicle_id: UUID,
    service: PartnerService = Depends(partner_service),
    _current_user: UserModel = Depends(require_role("admin")),
) -> dict:
    return await service.unassign_vehicle(partner_id, vehicle_id)


@router.get("/me")
async def get_my_partners(
    service: PartnerService = Depends(partner_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict:
    return await service.get_my_partners(current_user.id)
