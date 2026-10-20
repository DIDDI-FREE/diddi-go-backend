"""Adapter from DiddiGo's stable local scores to ``diddi.score.v1``.

The shared contract standardizes transport only. Formula ownership remains in
``ScoringService`` so no cross-module consumer can influence matching or local
reputation calculations.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Literal

CONTRACT_VERSION = "diddi.score.v1"
SERVICE = "diddigo"
_REASON_CODE = re.compile(r"^[a-z][a-z0-9_]*$")

_NORMALIZED_LEVELS = {
    "new": "unknown",
    "excellent": "excellent",
    "good": "good",
    "fair": "watch",
    "risk": "risk",
}


def adapt_personal_score(*, user_id: str, payload: Mapping[str, object]) -> dict:
    """Return one reliability envelope for a passenger or driver score."""
    return _adapt(
        kind="reliability",
        subject_type=str(payload["subject_type"]),
        subject_id=str(payload["subject_id"]),
        user_id=user_id,
        payload=payload,
        calculation_version="diddigo_reliability_v1",
    )


def adapt_trip_score(payload: Mapping[str, object]) -> dict:
    """Return one quality envelope for a ride without assigning it to one user."""
    return _adapt(
        kind="quality",
        subject_type="trip",
        subject_id=str(payload["ride_id"]),
        user_id=None,
        payload=payload,
        calculation_version="diddigo_trip_quality_v1",
    )


def _adapt(
    *,
    kind: Literal["reliability", "quality"],
    subject_type: str,
    subject_id: str,
    user_id: str | None,
    payload: Mapping[str, object],
    calculation_version: str,
) -> dict:
    value = float(payload["score_value"])
    local_level = str(payload["score_level"])
    return {
        "contract_version": CONTRACT_VERSION,
        "service": SERVICE,
        "kind": kind,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "user_id": user_id,
        "score": {
            "value": value,
            "scale": "five",
            "normalized_value": round(value * 20, 2),
            "local_level": local_level,
            "normalized_level": _NORMALIZED_LEVELS[local_level],
            "data_status": payload["score_status"],
            "sample_size": int(payload["sample_size"]),
            "reason_codes": _safe_reason_codes(payload.get("reason_codes", [])),
            "calculation_version": calculation_version,
            "calculated_at": payload["last_calculated_at"],
        },
    }


def _safe_reason_codes(values: object) -> list[str]:
    """Keep contract-safe, non-PII codes; collapse legacy free-text reasons."""
    codes: list[str] = []
    for value in values if isinstance(values, list) else []:
        code = str(value)
        if not _REASON_CODE.fullmatch(code):
            code = "reason_recorded"
        if code not in codes:
            codes.append(code)
    return codes
