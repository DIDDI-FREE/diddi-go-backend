"""SCRUM-63 Phase 3 — driver priority engine.

Covers the policy formula, the windowed reader, the capped matcher integration
(UC-284: a far driver can never outrank a nearer one), graceful degradation to
ETA-only, and the single ledger writer's event mapping.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app_base.modules.ride.application.matching_service import MatchingService
from app_base.modules.ride.application.priority_service import DriverPriorityService, PriorityLedger
from app_base.modules.ride.domain.entities import (
    ComfortLevel,
    Ride,
    RideStatus,
    VehicleCategory,
)
from app_base.modules.ride.domain.priority import (
    DEFAULT_ZONE_ID,
    DispatchConfig,
    PriorityEvent,
    PriorityEventKind,
    PriorityPolicy,
    PriorityScore,
)
from app_base.shared_kernel.types import GeoPoint

pytestmark = pytest.mark.unit


def _cfg(**over) -> DispatchConfig:
    base = {
        "search_radius_km": 5.0,
        "search_radius_step_km": 2.0,
        "search_radius_max_km": 15.0,
        "offer_wave_size": 5,
        "search_budget_seconds": 120,
        "eta_shortlist_size": 10,
        "priority_window_days": 7,
        "priority_cap_seconds": 120,
        "priority_seconds_per_point": 10,
        "points_ride_completed": 1,
        "points_ride_cancelled_by_driver": -3,
    }
    base.update(over)
    return DispatchConfig(**base)


# ---- 1. policy formula ------------------------------------------------------

def test_policy_points_and_bonus_formula() -> None:
    policy = PriorityPolicy(_cfg(points_ride_completed=2, points_ride_cancelled_by_driver=-5,
                                 priority_seconds_per_point=10))
    assert policy.points_for_ride_outcome(PriorityEventKind.RIDE_COMPLETED) == 2
    assert policy.points_for_ride_outcome(PriorityEventKind.RIDE_CANCELLED_BY_DRIVER) == -5
    assert policy.points_for_ride_outcome(PriorityEventKind.TEMP_BOOST) == 0
    assert policy.bonus_seconds(3) == 30
    assert policy.bonus_seconds(-2) == -20  # penalty passes through (worse rank)


# ---- 2. windowed reader -----------------------------------------------------

class FakeLedgerRepo:
    def __init__(self, totals=None, appended=None) -> None:
        self.totals = totals or {}
        self.appended: list[PriorityEvent] = appended if appended is not None else []
        self.query = None

    async def windowed_points(self, driver_ids, *, since, zone_id, now):
        self.query = {"driver_ids": driver_ids, "since": since, "zone_id": zone_id, "now": now}
        return {d: p for d, p in self.totals.items() if d in driver_ids}

    async def append(self, event: PriorityEvent) -> None:
        self.appended.append(event)


@pytest.mark.asyncio
async def test_reader_windows_and_maps_scores() -> None:
    d1, d2 = uuid4(), uuid4()
    repo = FakeLedgerRepo(totals={d1: 5, d2: -3})
    at = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
    svc = DriverPriorityService(repo, _cfg(priority_window_days=7))

    scores = await svc.scores_for([d1, d2], zone_id=DEFAULT_ZONE_ID, at=at)

    assert scores[d1] == PriorityScore(d1, 5)
    assert scores[d2] == PriorityScore(d2, -3)
    assert repo.query["since"] == at - timedelta(days=7)
    assert repo.query["zone_id"] == DEFAULT_ZONE_ID


# ---- 3 & 4. matcher integration (cap + degrade) -----------------------------

class FakeLocations:
    def __init__(self, coords):
        self.coords = coords

    async def find_available_nearby(self, location, radius_km, limit=20):
        return list(self.coords)

    async def coordinates_for(self, user_ids):
        return {u: self.coords[u] for u in user_ids if u in self.coords}


class FakeRouting:
    def __init__(self, eta_by_lat):
        self.eta_by_lat = eta_by_lat

    async def estimate(self, origin, destination, profile):
        from types import SimpleNamespace
        return SimpleNamespace(distance_km=1.0, duration_seconds=self.eta_by_lat[origin.lat])


class FakeDriverRepo:
    async def profile_ids_for_users(self, user_ids):
        return {u: u for u in user_ids}  # identity: test keys profiles == users


class FakePriority:
    def __init__(self, points, seconds_per_point=10):
        self.points = points
        self.spp = seconds_per_point

    async def scores_for(self, driver_ids, *, zone_id, at):
        return {d: PriorityScore(d, self.points[d]) for d in driver_ids if d in self.points}

    def bonus_seconds(self, points):
        return points * self.spp


def _ride():
    return Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        status=RideStatus.REQUESTED,
        pickup_location=GeoPoint(lat=9.9, lng=0.0),
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.STANDARD,
    )


def _matcher(coords, eta_by_lat, priority):
    return MatchingService(
        ride_repo=None, driver_repo=FakeDriverRepo(), vehicle_repo=None,
        locations=FakeLocations(coords), offers=None,
        routing=FakeRouting(eta_by_lat), priority=priority, config=_cfg(priority_cap_seconds=120),
    )


@pytest.mark.asyncio
async def test_priority_reorders_within_cap_but_never_beats_proximity() -> None:
    a, b, c = uuid4(), uuid4(), uuid4()  # near / mid / far
    coords = {a: GeoPoint(lat=0.0, lng=0.0), b: GeoPoint(lat=1.0, lng=0.0), c: GeoPoint(lat=2.0, lng=0.0)}
    eta_by_lat = {0.0: 100, 1.0: 130, 2.0: 300}
    # b has enough points to pass a (130-50=80 < 100); c has huge points but the
    # 120s cap leaves it at 300-120=180 — still last. Proximity stays dominant.
    matcher = _matcher(coords, eta_by_lat, FakePriority({a: 0, b: 5, c: 100}))

    ranked = await matcher._rank_by_eta(_ride(), [a, b, c])

    assert ranked == [b, a, c]


@pytest.mark.asyncio
async def test_matcher_degrades_to_eta_only_without_priority() -> None:
    a, b, c = uuid4(), uuid4(), uuid4()
    coords = {a: GeoPoint(lat=0.0, lng=0.0), b: GeoPoint(lat=1.0, lng=0.0), c: GeoPoint(lat=2.0, lng=0.0)}
    eta_by_lat = {0.0: 100, 1.0: 130, 2.0: 300}
    matcher = _matcher(coords, eta_by_lat, priority=None)

    ranked = await matcher._rank_by_eta(_ride(), [a, b, c])

    assert ranked == [a, b, c]


# ---- 5. ledger writer -------------------------------------------------------

def _outcome_ride(status, *, with_driver=True):
    return Ride(
        id=uuid4(),
        passenger_user_id=uuid4(),
        driver_id=uuid4() if with_driver else None,
        status=status,
        vehicle_category=VehicleCategory.STANDARD,
        comfort_level=ComfortLevel.STANDARD,
    )


@pytest.mark.asyncio
async def test_ledger_records_expected_kind_per_outcome() -> None:
    repo = FakeLedgerRepo()
    ledger = PriorityLedger(repo, _cfg(points_ride_completed=1, points_ride_cancelled_by_driver=-3))

    await ledger.record_ride_outcome(_outcome_ride(RideStatus.COMPLETED))
    await ledger.record_ride_outcome(_outcome_ride(RideStatus.CANCELLED_BY_DRIVER))
    await ledger.record_ride_outcome(_outcome_ride(RideStatus.CANCELLED_BY_PASSENGER))  # no-op
    await ledger.record_ride_outcome(_outcome_ride(RideStatus.COMPLETED, with_driver=False))  # no-op

    assert [(e.kind, e.points) for e in repo.appended] == [
        (PriorityEventKind.RIDE_COMPLETED, 1),
        (PriorityEventKind.RIDE_CANCELLED_BY_DRIVER, -3),
    ]
    assert all(e.zone_id == DEFAULT_ZONE_ID for e in repo.appended)
