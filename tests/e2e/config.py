"""Environment-driven configuration for the dispatch E2E suite (SCRUM-63).

Everything that could be a secret or environment-specific is read from the
process environment — nothing is hardcoded. The suite is skipped (never failed)
when the credentials it needs are absent, so a plain `pytest` run is unaffected.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

BASE_URL = os.getenv("DIDDIGO_E2E_BASE_URL", "https://go-staging.diddifree.com").rstrip("/")


def _ws_url(base: str) -> str:
    return base.replace("https://", "wss://").replace("http://", "ws://") + "/v1/ws"


@dataclass(frozen=True)
class E2EConfig:
    base_url: str = BASE_URL
    ws_url: str = field(default_factory=lambda: _ws_url(BASE_URL))

    # Passenger + admin identities (the admin MUST already be role=admin on the
    # target env — it approves driver KYC and vehicle KYV).
    passenger_phone: str = os.getenv("DIDDIGO_E2E_PASSENGER_PHONE", "+2250700000101")
    admin_phone: str = os.getenv("DIDDIGO_E2E_ADMIN_PHONE", "")

    # Drivers are numbered; phone pattern gets the index zero-padded to 2 digits.
    driver_phone_prefix: str = os.getenv("DIDDIGO_E2E_DRIVER_PHONE_PREFIX", "+225070000012")
    driver_count: int = int(os.getenv("DIDDIGO_E2E_DRIVER_COUNT", "3"))

    # S2S client-credentials for the /internal admin dispatch routes.
    s2s_token_url: str = os.getenv("DIDDIGO_S2S_TOKEN_URL", "")
    s2s_client_id: str = os.getenv("DIDDIGO_S2S_CLIENT_ID", "")
    s2s_client_secret: str = os.getenv("DIDDIGO_S2S_CLIENT_SECRET", "")
    s2s_audience: str = os.getenv("DIDDIGO_S2S_AUDIENCE", "diddigo")

    # Abidjan test geography.
    pickup_lat: float = float(os.getenv("DIDDIGO_E2E_PICKUP_LAT", "5.3364"))
    pickup_lng: float = float(os.getenv("DIDDIGO_E2E_PICKUP_LNG", "-4.0267"))
    dropoff_lat: float = float(os.getenv("DIDDIGO_E2E_DROPOFF_LAT", "5.3599"))
    dropoff_lng: float = float(os.getenv("DIDDIGO_E2E_DROPOFF_LNG", "-4.0083"))
    # A near driver (~80m from pickup) and a far driver (~5km) — separated enough
    # that ETA order tracks distance order despite real DiddiMap routing.
    near_lat: float = float(os.getenv("DIDDIGO_E2E_NEAR_LAT", "5.3370"))
    near_lng: float = float(os.getenv("DIDDIGO_E2E_NEAR_LNG", "-4.0270"))
    far_lat: float = float(os.getenv("DIDDIGO_E2E_FAR_LAT", "5.3000"))
    far_lng: float = float(os.getenv("DIDDIGO_E2E_FAR_LNG", "-3.9800"))
    # A remote pickup with (hopefully) no drivers around — density-gate test.
    remote_lat: float = float(os.getenv("DIDDIGO_E2E_REMOTE_LAT", "5.4200"))
    remote_lng: float = float(os.getenv("DIDDIGO_E2E_REMOTE_LNG", "-4.1100"))

    vehicle_category: str = os.getenv("DIDDIGO_E2E_VEHICLE_CATEGORY", "standard")
    comfort_level: str = os.getenv("DIDDIGO_E2E_COMFORT_LEVEL", "standard")
    payment_method: str = os.getenv("DIDDIGO_E2E_PAYMENT_METHOD", "cash")

    http_timeout: float = float(os.getenv("DIDDIGO_E2E_HTTP_TIMEOUT", "20"))
    ws_collect_seconds: float = float(os.getenv("DIDDIGO_E2E_WS_COLLECT_SECONDS", "8"))

    def driver_phone(self, index: int) -> str:
        suffix = f"{index:d}" if self.driver_count < 10 else f"{index:02d}"
        return f"{self.driver_phone_prefix}{suffix}"

    def missing_prerequisites(self) -> list[str]:
        """Human-readable list of env vars needed to run; empty means runnable."""
        missing: list[str] = []
        if not self.admin_phone:
            missing.append("DIDDIGO_E2E_ADMIN_PHONE (a staging account with role=admin)")
        for name, value in (
            ("DIDDIGO_S2S_TOKEN_URL", self.s2s_token_url),
            ("DIDDIGO_S2S_CLIENT_ID", self.s2s_client_id),
            ("DIDDIGO_S2S_CLIENT_SECRET", self.s2s_client_secret),
        ):
            if not value:
                missing.append(name)
        return missing


CONFIG = E2EConfig()
