"""Driver priority engine — domain (SCRUM-63 Phase 3).

Priority nudges dispatch ranking without ever overriding proximity. The design
has four single-responsibility seams so point logic never leaks across the
codebase:

  * ``PriorityEvent`` — one append-only fact (the ledger row).
  * ``PriorityPolicy`` — the ONLY place that decides how many points an event
    is worth and how a windowed point total converts to an ETA-seconds bonus.
  * the ledger writer records events; the reader sums them over a window.
  * the matcher subtracts a *capped* bonus from ETA (UC-284) — proximity stays
    dominant.

Zones: one big zone for now (SCRUM-83 will add real zones + resolution). Ride
outcomes are tagged with ``DEFAULT_ZONE_ID``; global rules use ``zone_id=None``.
Only zone *resolution* changes when SCRUM-83 lands — schema and queries are
already zone-shaped.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

# The single implicit service zone until SCRUM-83 introduces real zones.
DEFAULT_ZONE_ID = UUID("00000000-0000-0000-0000-0000000000d6")


class PriorityEventKind(str, Enum):
    """Why a driver's priority moved. Ride outcomes are derived signals
    (UC-108/109); temp boosts are explicit admin grants (UC-106)."""

    RIDE_COMPLETED = "ride_completed"
    RIDE_CANCELLED_BY_DRIVER = "ride_cancelled_by_driver"
    TEMP_BOOST = "temp_boost"


@dataclass(frozen=True)
class DispatchConfig:
    """Tunable dispatch knobs — DB-backed and editable without redeploy
    (UC-288), seeded from settings defaults."""

    search_radius_km: float
    search_radius_step_km: float
    search_radius_max_km: float
    offer_wave_size: int
    search_budget_seconds: int
    eta_shortlist_size: int
    priority_window_days: int
    priority_cap_seconds: int
    priority_seconds_per_point: int
    points_ride_completed: int
    points_ride_cancelled_by_driver: int


@dataclass(frozen=True)
class PriorityEvent:
    """One append-only ledger fact for a driver (keyed by driver_profile_id)."""

    driver_id: UUID
    kind: PriorityEventKind
    points: int
    zone_id: UUID | None = None
    ride_id: UUID | None = None
    reason: str | None = None
    expires_at: datetime | None = None


@dataclass(frozen=True)
class PriorityScore:
    """A driver's windowed point total (may be negative for frequent
    cancellers)."""

    driver_id: UUID
    points: int


class PriorityPolicy:
    """Pure: the ONLY owner of the points formula and the point→seconds
    conversion. Given a config, no other module does priority arithmetic."""

    def __init__(self, config: DispatchConfig) -> None:
        self._config = config

    def points_for_ride_outcome(self, kind: PriorityEventKind) -> int:
        if kind is PriorityEventKind.RIDE_COMPLETED:
            return self._config.points_ride_completed
        if kind is PriorityEventKind.RIDE_CANCELLED_BY_DRIVER:
            return self._config.points_ride_cancelled_by_driver
        return 0

    def bonus_seconds(self, points: int) -> int:
        """ETA-seconds advantage for a windowed point total.

        Positive points shave seconds off the effective ETA (better rank);
        negative points (frequent cancellers, UC-108) add seconds (worse rank).
        The caller caps only the positive side so a far driver can never
        outrank a nearer one (UC-284)."""
        return points * self._config.priority_seconds_per_point
