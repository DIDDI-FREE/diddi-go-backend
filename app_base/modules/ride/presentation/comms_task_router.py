from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.core.auth_deps import require_identity_service_token
from app_base.core.database import get_session
from app_base.core.service_scopes import COMMS_TASK_READ, DIDDIGO_AUDIENCE
from app_base.core.settings import settings
from app_base.modules.ride.application.comms_task_resolver import RideCommsTaskResolver

router = APIRouter(prefix="/internal/v1/comms", tags=["internal-comms"])
require_diddicomms = require_identity_service_token(
    audience=DIDDIGO_AUDIENCE,
    required_scope=COMMS_TASK_READ,
    expected_subject="service:diddicomms",
    expected_client_id=settings.diddicomms_service_client_id,
)


class CommsTaskReferenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_service: str
    task_type: str
    task_id: UUID


class CommsParticipantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID
    role: str
    phone_e164: str | None = None


class CommsTaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: CommsTaskReferenceResponse
    state: str
    version: int
    participants: list[CommsParticipantResponse]
    messaging_allowed: bool
    calling_allowed: bool
    closes_at: datetime | None = None


@router.get("/tasks/{task_type}/{task_id}", response_model=CommsTaskResponse)
async def get_comms_task(
    task_type: str,
    task_id: UUID,
    _claims: dict = Depends(require_diddicomms),
    session: AsyncSession = Depends(get_session),
) -> CommsTaskResponse:
    projection = await RideCommsTaskResolver(session).resolve(task_type=task_type, task_id=task_id)
    return CommsTaskResponse(
        task=CommsTaskReferenceResponse(
            owner_service=projection.owner_service,
            task_type=projection.task_type,
            task_id=projection.task_id,
        ),
        state=projection.state,
        version=projection.version,
        participants=[
            CommsParticipantResponse(
                user_id=participant.user_id,
                role=participant.role,
                phone_e164=participant.phone_e164,
            )
            for participant in projection.participants
        ],
        messaging_allowed=projection.messaging_allowed,
        calling_allowed=projection.calling_allowed,
        closes_at=projection.closes_at,
    )
