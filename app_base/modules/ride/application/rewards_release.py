"""Closing a DiddiRewards reservation (ticket 014).

Every reservation must end by exactly one of `confirm` (paid) or `release`.
These helpers are shared by the payment service (a confirm Rewards refuses for
good) and by the `rewards-reservations` sweep (calls that failed earlier).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.modules.ride.domain.entities import Ride, RideStatus

logger = logging.getLogger(__name__)

CONFIRMATION_REFUSED = "confirmation_refused"
# A reservation in one of these states needs no further call to Rewards.
CLOSED_STATUSES = frozenset({"confirmed", "corrected", "released", CONFIRMATION_REFUSED, "release_refused"})
ABANDONED_RIDE_STATUSES = frozenset(
    {RideStatus.CANCELLED_BY_PASSENGER, RideStatus.CANCELLED_BY_DRIVER, RideStatus.NO_DRIVER_FOUND}
)
# Rewards said no and will say no again. 401/403/408/429 and 5xx are worth a retry.
_FINAL_REFUSAL_STATUS_CODES = frozenset({400, 404, 409, 410, 422})


def is_final_refusal(exc: BaseException) -> bool:
    return isinstance(exc, ApiError) and exc.status_code in _FINAL_REFUSAL_STATUS_CODES


def release_reason(ride: Ride) -> str | None:
    """Reason to send when releasing `ride`'s reservation, or None if it must stay open.

    Derived from the ride alone so a retry sends the same reason as the first
    attempt: Rewards answers 409 to the same Idempotency-Key with another reason.
    """
    if (ride.rewards_discount_amount or Decimal("0")) <= 0:
        return "nothing_reserved"
    if ride.status is RideStatus.NO_DRIVER_FOUND:
        return "no_driver_found"
    if ride.status in ABANDONED_RIDE_STATUSES:
        return ride.cancellation_reason or "cancelled"
    if ride.status is RideStatus.COMPLETED:
        return CONFIRMATION_REFUSED
    return None


async def release_reservation(diddirewards: Any, ride_repo: Any, ride: Ride, *, reason: str) -> bool:
    """Release the reservation and record the outcome on the ride. True when Rewards freed it."""
    try:
        await diddirewards.release(
            reservation_id=ride.rewards_reservation_id,
            ride_id=ride.id,
            reason=reason,
            idempotency_key=f"diddigo:ride:{ride.id}:rewards-release:v1",
            request_id=str(ride.id),
        )
    except Exception as exc:
        refused = is_final_refusal(exc)
        ride.rewards_status = "release_refused" if refused else "release_deferred"
        await ride_repo.save(ride)
        logger.exception("rewards release %s ride_id=%s", "refused" if refused else "deferred", ride.id)
        log_event(
            "rewards.release.refused" if refused else "rewards.release.deferred",
            level="error",
            ride_id=ride.id,
            reason=reason,
        )
        return False
    ride.rewards_status = CONFIRMATION_REFUSED if reason == CONFIRMATION_REFUSED else "released"
    await ride_repo.save(ride)
    log_event("rewards.release.completed", ride_id=ride.id, reason=reason)
    return True
