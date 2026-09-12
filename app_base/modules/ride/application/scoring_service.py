from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.modules.ride.domain.entities import Ride, RideStatus
from app_base.modules.ride.domain.interfaces import DriverProfileRepository, RideRepository


@dataclass
class ScoringService:
    ride_repo: RideRepository
    driver_repo: DriverProfileRepository

    async def get_my_scores(self, user_id: UUID) -> dict:
        passenger_stats = await self.ride_repo.passenger_scoring_stats(user_id)
        driver_profile = await self.driver_repo.find_by_user_id(user_id)
        driver_score = None
        if driver_profile is not None:
            driver_stats = await self.ride_repo.driver_scoring_stats(driver_profile.id)
            driver_score = _score_payload(
                "driver",
                driver_stats,
                subject_id=driver_profile.id,
            )

        return {
            "user_id": str(user_id),
            "service": "diddigo",
            "passenger_score": _score_payload("passenger", passenger_stats, subject_id=user_id),
            "driver_score": driver_score,
        }

    async def get_ride_score(self, ride_id: UUID, *, actor_user_id: UUID, actor_role: str) -> dict:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, ErrorCode.RIDE_NOT_FOUND, "Aucune course trouvee avec cet identifiant.")
        if not await self._can_view_ride_score(ride, actor_user_id=actor_user_id, actor_role=actor_role):
            raise ApiError(403, ErrorCode.RIDE_NOT_OWNED_BY_USER, "Cette course ne vous appartient pas.")
        rating_summary = await self.ride_repo.ride_rating_summary(ride_id)
        return _trip_score_payload(ride, rating_summary)

    async def _can_view_ride_score(self, ride: Ride, *, actor_user_id: UUID, actor_role: str) -> bool:
        if actor_role == "admin":
            return True
        if ride.passenger_user_id == actor_user_id:
            return True
        profile = await self.driver_repo.find_by_user_id(actor_user_id)
        return bool(profile and ride.driver_id == profile.id)


def _score_payload(subject_type: str, stats: dict, *, subject_id: UUID) -> dict:
    total = int(stats.get("total_rides") or 0)
    completed = int(stats.get("completed_rides") or 0)
    cancelled = int(stats.get("cancelled_rides") or 0)
    emergencies = int(stats.get("emergency_reports") or 0)
    rating_count = int(stats.get("rating_count") or 0)
    rating_avg = stats.get("rating_avg")
    rating_value = Decimal(str(rating_avg)) if rating_avg is not None else Decimal("5.00")
    sample_size = total + rating_count

    completion_rate = Decimal(completed) / Decimal(total) if total else Decimal("0")
    cancellation_rate = Decimal(cancelled) / Decimal(total) if total else Decimal("0")
    score = (
        rating_value * Decimal("0.70")
        + completion_rate * Decimal("5.00") * Decimal("0.20")
        + (Decimal("1.00") - cancellation_rate) * Decimal("5.00") * Decimal("0.10")
        - Decimal(min(emergencies, 3)) * Decimal("0.15")
    )
    score = max(Decimal("1.00"), min(Decimal("5.00"), score)).quantize(Decimal("0.01"))

    reason_codes = _reason_codes(
        total=total,
        completed=completed,
        cancelled=cancelled,
        emergencies=emergencies,
        rating_avg=rating_value if rating_count else None,
        sample_size=sample_size,
    )

    return {
        "subject_type": subject_type,
        "subject_id": str(subject_id),
        "score_value": float(score),
        "score_level": _score_level(score, sample_size=sample_size),
        "score_status": "insufficient_data" if sample_size < 5 else "stable",
        "reason_codes": reason_codes,
        "last_calculated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "sample_size": sample_size,
        "metrics": {
            "total_rides": total,
            "completed_rides": completed,
            "cancelled_rides": cancelled,
            "emergency_reports": emergencies,
            "rating_count": rating_count,
            "rating_avg": float(rating_value) if rating_count else None,
        },
    }


def _trip_score_payload(ride: Ride, rating_summary: dict) -> dict:
    rating_count = int(rating_summary.get("rating_count") or 0)
    rating_avg = rating_summary.get("rating_avg")
    rating_value = Decimal(str(rating_avg)) if rating_avg is not None else None
    score = _base_trip_score(ride)
    if rating_value is not None:
        score = (score * Decimal("0.60") + rating_value * Decimal("0.40")).quantize(Decimal("0.01"))
    if ride.emergency_status:
        score -= Decimal("0.75")
    score = max(Decimal("1.00"), min(Decimal("5.00"), score)).quantize(Decimal("0.01"))
    reason_codes = _trip_reason_codes(ride, rating_count=rating_count, rating_avg=rating_value)

    return {
        "ride_id": str(ride.id),
        "subject_type": "trip",
        "score_value": float(score),
        "score_level": _score_level(score, sample_size=max(1, rating_count)),
        "score_status": "stable" if ride.status is RideStatus.COMPLETED else "provisional",
        "reason_codes": reason_codes,
        "last_calculated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "sample_size": rating_count,
        "metrics": {
            "ride_status": ride.status.value,
            "rating_count": rating_count,
            "rating_avg": float(rating_value) if rating_value is not None else None,
            "emergency_status": ride.emergency_status,
            "cancellation_reason": ride.cancellation_reason,
        },
    }


def _base_trip_score(ride: Ride) -> Decimal:
    if ride.status is RideStatus.COMPLETED:
        return Decimal("5.00")
    if ride.status in {RideStatus.CANCELLED_BY_DRIVER, RideStatus.CANCELLED_BY_PASSENGER}:
        return Decimal("2.75")
    if ride.status is RideStatus.NO_DRIVER_FOUND:
        return Decimal("3.00")
    return Decimal("4.00")


def _score_level(score: Decimal, *, sample_size: int) -> str:
    if sample_size < 5:
        return "new"
    if score >= Decimal("4.70"):
        return "excellent"
    if score >= Decimal("4.20"):
        return "good"
    if score >= Decimal("3.50"):
        return "fair"
    return "risk"


def _reason_codes(
    *,
    total: int,
    completed: int,
    cancelled: int,
    emergencies: int,
    rating_avg: Decimal | None,
    sample_size: int,
) -> list[str]:
    reasons: list[str] = []
    if total == 0:
        reasons.append("no_activity")
    if sample_size < 5:
        reasons.append("insufficient_data")
    if rating_avg is not None:
        if rating_avg >= Decimal("4.70"):
            reasons.append("good_ratings")
        elif rating_avg < Decimal("3.50"):
            reasons.append("low_ratings")
    if total:
        cancellation_rate = Decimal(cancelled) / Decimal(total)
        completion_rate = Decimal(completed) / Decimal(total)
        if cancellation_rate > Decimal("0.20"):
            reasons.append("high_cancellation")
        elif cancellation_rate <= Decimal("0.05"):
            reasons.append("low_cancellation")
        if completion_rate >= Decimal("0.80"):
            reasons.append("reliable_completion")
        elif completion_rate < Decimal("0.50"):
            reasons.append("low_completion")
    if emergencies:
        reasons.append("emergency_reports")
    return reasons


def _trip_reason_codes(ride: Ride, *, rating_count: int, rating_avg: Decimal | None) -> list[str]:
    reasons = [f"status_{ride.status.value}"]
    if rating_count == 0:
        reasons.append("no_ratings")
    elif rating_avg is not None and rating_avg >= Decimal("4.70"):
        reasons.append("good_ratings")
    elif rating_avg is not None and rating_avg < Decimal("3.50"):
        reasons.append("low_ratings")
    if ride.emergency_status:
        reasons.append("emergency_reported")
    if ride.cancellation_reason:
        reasons.append(f"cancel_reason_{ride.cancellation_reason}")
    return reasons
