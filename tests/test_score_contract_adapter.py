from __future__ import annotations

import pytest

from app_base.modules.ride.application.score_contract_adapter import adapt_personal_score, adapt_trip_score

pytestmark = pytest.mark.unit


def test_personal_score_is_adapted_without_changing_its_formula() -> None:
    result = adapt_personal_score(
        user_id="11111111-1111-1111-1111-111111111111",
        payload={
            "subject_type": "driver",
            "subject_id": "22222222-2222-2222-2222-222222222222",
            "score_value": 4.25,
            "score_level": "good",
            "score_status": "stable",
            "sample_size": 8,
            "reason_codes": ["good_ratings", "low_cancellation"],
            "last_calculated_at": "2026-10-20T10:00:00Z",
        },
    )

    assert result == {
        "contract_version": "diddi.score.v1",
        "service": "diddigo",
        "kind": "reliability",
        "subject_type": "driver",
        "subject_id": "22222222-2222-2222-2222-222222222222",
        "user_id": "11111111-1111-1111-1111-111111111111",
        "score": {
            "value": 4.25,
            "scale": "five",
            "normalized_value": 85.0,
            "local_level": "good",
            "normalized_level": "good",
            "data_status": "stable",
            "sample_size": 8,
            "reason_codes": ["good_ratings", "low_cancellation"],
            "calculation_version": "diddigo_reliability_v1",
            "calculated_at": "2026-10-20T10:00:00Z",
        },
    }


def test_new_score_stays_neutral_but_normalizes_to_unknown() -> None:
    result = adapt_personal_score(
        user_id="11111111-1111-1111-1111-111111111111",
        payload={
            "subject_type": "passenger",
            "subject_id": "11111111-1111-1111-1111-111111111111",
            "score_value": 4.0,
            "score_level": "new",
            "score_status": "insufficient_data",
            "sample_size": 0,
            "reason_codes": ["no_activity", "insufficient_data"],
            "last_calculated_at": "2026-10-20T10:00:00Z",
        },
    )

    assert result["score"]["normalized_value"] == 80.0
    assert result["score"]["normalized_level"] == "unknown"
    assert result["score"]["data_status"] == "insufficient_data"


def test_trip_score_is_quality_and_has_no_user_owner() -> None:
    result = adapt_trip_score(
        {
            "ride_id": "33333333-3333-3333-3333-333333333333",
            "score_value": 3.5,
            "score_level": "fair",
            "score_status": "provisional",
            "sample_size": 1,
            "reason_codes": ["status_in_progress"],
            "last_calculated_at": "2026-10-20T10:00:00Z",
        }
    )

    assert result["kind"] == "quality"
    assert result["subject_type"] == "trip"
    assert result["user_id"] is None
    assert result["score"]["normalized_level"] == "watch"
    assert result["score"]["calculation_version"] == "diddigo_trip_quality_v1"


def test_legacy_free_text_reason_is_not_exposed_as_a_contract_code() -> None:
    result = adapt_trip_score(
        {
            "ride_id": "33333333-3333-3333-3333-333333333333",
            "score_value": 2.75,
            "score_level": "risk",
            "score_status": "provisional",
            "sample_size": 0,
            "reason_codes": ["cancel_reason_client changed address", "cancel_reason_client changed address"],
            "last_calculated_at": "2026-10-20T10:00:00Z",
        }
    )

    assert result["score"]["reason_codes"] == ["reason_recorded"]
