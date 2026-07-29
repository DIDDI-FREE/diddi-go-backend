"""Unit tests for the ride state machine — pure domain, no DB or HTTP.

The transition table lives in `ride/domain/entities.py` (architecture doc §4):

    requested → matched → driver_en_route → in_progress → completed
        ↓            ↓
    no_driver_found  cancelled_by_passenger / cancelled_by_driver
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app_base.modules.ride.domain.entities import (
    ALLOWED_TRANSITIONS,
    InvalidStatusTransition,
    Ride,
    RideStatus,
)


def make_ride(status: RideStatus = RideStatus.REQUESTED) -> Ride:
    return Ride(
        id=Ride.new_id(),
        passenger_user_id=uuid4(),
        status=status,
        requested_at=datetime.now(UTC),
        estimated_fare=Decimal("2500"),
    )


@pytest.mark.parametrize(
    ("start", "target"),
    [
        (RideStatus.REQUESTED, RideStatus.MATCHED),
        (RideStatus.REQUESTED, RideStatus.NO_DRIVER_FOUND),
        (RideStatus.REQUESTED, RideStatus.CANCELLED_BY_PASSENGER),
        (RideStatus.MATCHED, RideStatus.DRIVER_EN_ROUTE),
        (RideStatus.MATCHED, RideStatus.CANCELLED_BY_DRIVER),
        (RideStatus.DRIVER_EN_ROUTE, RideStatus.IN_PROGRESS),
        (RideStatus.IN_PROGRESS, RideStatus.COMPLETED),
    ],
)
def test_valid_transitions_are_accepted(start: RideStatus, target: RideStatus) -> None:
    ride = make_ride(start)
    ride.transition(target)
    assert ride.status is target


@pytest.mark.parametrize(
    ("start", "target"),
    [
        # Cannot skip the matching step.
        (RideStatus.REQUESTED, RideStatus.DRIVER_EN_ROUTE),
        (RideStatus.REQUESTED, RideStatus.IN_PROGRESS),
        (RideStatus.REQUESTED, RideStatus.COMPLETED),
        # Cannot move backwards.
        (RideStatus.IN_PROGRESS, RideStatus.MATCHED),
        (RideStatus.DRIVER_EN_ROUTE, RideStatus.REQUESTED),
        # Terminal states are terminal.
        (RideStatus.COMPLETED, RideStatus.IN_PROGRESS),
        (RideStatus.CANCELLED_BY_PASSENGER, RideStatus.MATCHED),
        (RideStatus.NO_DRIVER_FOUND, RideStatus.MATCHED),
    ],
)
def test_invalid_transitions_raise(start: RideStatus, target: RideStatus) -> None:
    ride = make_ride(start)
    with pytest.raises(InvalidStatusTransition):
        ride.transition(target)
    assert ride.status is start, "status must not change on a rejected transition"


def test_same_status_transition_is_a_noop() -> None:
    ride = make_ride(RideStatus.MATCHED)
    ride.transition(RideStatus.MATCHED)
    assert ride.status is RideStatus.MATCHED
    assert ride.status_history == []


def test_terminal_states_have_no_outgoing_transitions() -> None:
    for terminal in (
        RideStatus.COMPLETED,
        RideStatus.CANCELLED_BY_PASSENGER,
        RideStatus.CANCELLED_BY_DRIVER,
        RideStatus.NO_DRIVER_FOUND,
    ):
        assert ALLOWED_TRANSITIONS[terminal] == set()


def test_timestamps_are_stamped_on_first_visit() -> None:
    ride = make_ride()
    assert ride.matched_at is None

    ride.transition(RideStatus.MATCHED)
    matched_at = ride.matched_at
    assert matched_at is not None

    ride.transition(RideStatus.DRIVER_EN_ROUTE)
    assert ride.matched_at == matched_at, "matched_at must not be overwritten"

    ride.transition(RideStatus.IN_PROGRESS)
    assert ride.started_at is not None

    ride.transition(RideStatus.COMPLETED)
    assert ride.completed_at is not None


def test_completion_defaults_final_fare_to_estimate() -> None:
    ride = make_ride()
    ride.transition(RideStatus.MATCHED)
    ride.transition(RideStatus.DRIVER_EN_ROUTE)
    ride.transition(RideStatus.IN_PROGRESS)
    assert ride.final_fare is None

    ride.transition(RideStatus.COMPLETED)
    assert ride.final_fare == Decimal("2500")


def test_cancellation_stamps_cancelled_at() -> None:
    ride = make_ride(RideStatus.MATCHED)
    ride.transition(RideStatus.CANCELLED_BY_PASSENGER, metadata={"reason": "passenger_no_show"})
    assert ride.cancelled_at is not None
    assert ride.status is RideStatus.CANCELLED_BY_PASSENGER


def test_history_records_each_transition() -> None:
    ride = make_ride()
    ride.transition(RideStatus.MATCHED)
    ride.transition(RideStatus.DRIVER_EN_ROUTE)

    assert len(ride.status_history) == 2
    first, second = ride.status_history
    assert (first.from_status, first.to_status) == (RideStatus.REQUESTED, RideStatus.MATCHED)
    assert (second.from_status, second.to_status) == (RideStatus.MATCHED, RideStatus.DRIVER_EN_ROUTE)
    assert all(t.ride_id == ride.id for t in ride.status_history)


def test_is_active_property() -> None:
    assert make_ride(RideStatus.REQUESTED).is_active is True
    assert make_ride(RideStatus.IN_PROGRESS).is_active is True
    assert make_ride(RideStatus.COMPLETED).is_active is False
    assert make_ride(RideStatus.NO_DRIVER_FOUND).is_active is False
