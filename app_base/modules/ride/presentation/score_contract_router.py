"""Internal diddi.score.v1 adapter for DiddiFree Pro."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app_base.core.auth_deps import require_identity_service_token
from app_base.core.deps import scoring_service
from app_base.core.service_scopes import DIDDIGO_AUDIENCE, SCORES_READ
from app_base.core.settings import settings
from app_base.modules.ride.application.score_contract_adapter import (
    adapt_personal_score,
    adapt_trip_score,
)
from app_base.modules.ride.application.scoring_service import ScoringService

router = APIRouter(prefix="/internal/v1/scores", tags=["internal-scores"])
require_diddifreepro = require_identity_service_token(
    audience=DIDDIGO_AUDIENCE,
    required_scope=SCORES_READ,
    expected_subject="service:diddifreepro",
    expected_client_id=settings.diddifreepro_service_client_id,
)


class DiddiScoreValueResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float | None
    scale: Literal["five", "hundred"]
    normalized_value: float | None = Field(default=None, ge=0, le=100)
    local_level: str
    normalized_level: Literal["excellent", "good", "watch", "risk", "unknown"]
    data_status: Literal["stable", "provisional", "insufficient_data", "stale", "disabled", "blocked"]
    sample_size: int = Field(ge=0)
    reason_codes: list[str]
    calculation_version: str
    calculated_at: datetime


class DiddiScoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: Literal["diddi.score.v1"]
    service: Literal["diddigo"]
    kind: Literal["reliability", "risk", "quality"]
    subject_type: str
    subject_id: str
    user_id: UUID | None
    score: DiddiScoreValueResponse


class DiddiScoreCollectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scores: list[DiddiScoreResponse]


@router.get("/users/{user_id}", response_model=DiddiScoreCollectionResponse)
async def get_user_scores_contract(
    user_id: UUID,
    _claims: dict = Depends(require_diddifreepro),
    service: ScoringService = Depends(scoring_service),
) -> DiddiScoreCollectionResponse:
    local = await service.get_my_scores(user_id)
    scores = [adapt_personal_score(user_id=str(user_id), payload=local["passenger_score"])]
    if local["driver_score"] is not None:
        scores.append(adapt_personal_score(user_id=str(user_id), payload=local["driver_score"]))
    return DiddiScoreCollectionResponse(scores=scores)


@router.get("/rides/{ride_id}", response_model=DiddiScoreResponse)
async def get_ride_score_contract(
    ride_id: UUID,
    _claims: dict = Depends(require_diddifreepro),
    service: ScoringService = Depends(scoring_service),
) -> DiddiScoreResponse:
    return DiddiScoreResponse.model_validate(adapt_trip_score(await service.get_ride_score_for_internal(ride_id)))
