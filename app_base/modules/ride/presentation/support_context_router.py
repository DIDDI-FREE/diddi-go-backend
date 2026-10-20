"""DiddiSupport's scoped, redacted read-only ride context endpoint."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.auth_deps import require_identity_service_token
from app_base.core.database import get_session
from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.core.service_scopes import DIDDIGO_AUDIENCE, SUPPORT_CONTEXT_READ
from app_base.core.settings import settings
from app_base.modules.ride.application.support_context_resolver import RideSupportContextResolver

router = APIRouter(prefix="/internal/v1/support", tags=["internal-support"])
require_diddisupport = require_identity_service_token(
    audience=DIDDIGO_AUDIENCE,
    required_scope=SUPPORT_CONTEXT_READ,
    expected_subject="service:diddisupport",
    expected_client_id=settings.diddisupport_service_client_id,
)

REDACTED_FIELDS = [
    "participants.phone_e164",
    "locations.pickup",
    "locations.dropoff",
    "driver.last_location",
    "kyc",
    "payment.provider_details",
]


class SupportParticipantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    role: Literal["passenger", "driver"]


class SupportRideTimelineResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requested_at: datetime | None = None
    matched_at: datetime | None = None
    arrived_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None


class SupportRideDataResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    completion_reason: str | None = None
    cancellation_reason: str | None = None
    fare_amount: Decimal | None = Field(default=None, description="Montant final si disponible, sinon montant estimé.")
    currency: str
    payment_method: str
    participants: list[SupportParticipantResponse]
    timeline: SupportRideTimelineResponse


class SupportRideContextResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    protocol: Literal["diddi.context.v1"]
    origin_service: Literal["diddigo"]
    resource_type: Literal["ride"]
    resource_id: UUID
    data: SupportRideDataResponse
    redacted_fields: list[str]
    as_of: datetime
    fetched_at: datetime


async def require_support_context_scope_header(
    x_support_context_scope: str | None = Header(default=None, alias="X-Support-Context-Scope"),
) -> None:
    """Validate the protocol header; authorization still comes from the JWT scope."""
    if x_support_context_scope != SUPPORT_CONTEXT_READ:
        raise ApiError(403, ErrorCode.SERVICE_SCOPE_HEADER_INVALID, "Le scope de contexte Support est invalide.")


@router.get("/ride/{ride_id}/context", response_model=SupportRideContextResponse)
async def get_ride_support_context(
    ride_id: UUID,
    request: Request,
    _claims: dict = Depends(require_diddisupport),
    _scope_header: None = Depends(require_support_context_scope_header),
    session: AsyncSession = Depends(get_session),
) -> SupportRideContextResponse:
    projection = await RideSupportContextResolver(session).resolve(ride_id)
    fetched_at = datetime.now(UTC)
    request_id = getattr(request.state, "request_id", None)
    log_event(
        "support.context.ride.fetched",
        request_id=request_id,
        ride_id=str(ride_id),
        ride_status=projection.status,
    )
    return SupportRideContextResponse(
        protocol="diddi.context.v1",
        origin_service="diddigo",
        resource_type="ride",
        resource_id=projection.ride_id,
        data=SupportRideDataResponse(
            status=projection.status,
            completion_reason=projection.completion_reason,
            cancellation_reason=projection.cancellation_reason,
            fare_amount=projection.fare_amount,
            currency=projection.currency,
            payment_method=projection.payment_method,
            participants=[
                SupportParticipantResponse(user_id=item.user_id, role=item.role)
                for item in projection.participants
            ],
            timeline=SupportRideTimelineResponse(
                requested_at=projection.requested_at,
                matched_at=projection.matched_at,
                arrived_at=projection.arrived_at,
                started_at=projection.started_at,
                completed_at=projection.completed_at,
                cancelled_at=projection.cancelled_at,
            ),
        ),
        redacted_fields=REDACTED_FIELDS,
        as_of=projection.as_of,
        fetched_at=fetched_at,
    )
