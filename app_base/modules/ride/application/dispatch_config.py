"""Dispatch tunables — the seed defaults and the settings→config builder.

Kept in the application layer (not infra) so both the matcher and the infra
config store can build a ``DispatchConfig`` from settings without an
application→infra import or a circular import through ``matching_service``.
"""

from __future__ import annotations

from app_base.core.settings import Settings
from app_base.modules.ride.domain.priority import DispatchConfig

# Baseline knobs. The DB-backed dispatch_config (UC-288) overrides these at
# runtime; they are the seed defaults and the values tests assert against.
SEARCH_RADIUS_KM = 5.0
OFFER_WAVE_SIZE = 5


def dispatch_config_from_settings(settings: Settings) -> DispatchConfig:
    return DispatchConfig(
        search_radius_km=SEARCH_RADIUS_KM,
        search_radius_step_km=settings.matching_search_radius_step_km,
        search_radius_max_km=settings.matching_search_radius_max_km,
        offer_wave_size=OFFER_WAVE_SIZE,
        search_budget_seconds=settings.matching_search_budget_seconds,
        eta_shortlist_size=settings.matching_eta_shortlist_size,
        priority_window_days=settings.matching_priority_window_days,
        priority_cap_seconds=settings.matching_priority_cap_seconds,
        priority_seconds_per_point=settings.matching_priority_seconds_per_point,
        points_ride_completed=settings.matching_priority_points_ride_completed,
        points_ride_cancelled_by_driver=settings.matching_priority_points_ride_cancelled_by_driver,
    )
