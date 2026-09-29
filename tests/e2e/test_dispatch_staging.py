"""End-to-end tests for the DiddiGo dispatch engine (SCRUM-63) against the LIVE
staging API.

These are DESELECTED by default (`addopts = -m 'not e2e'`) and skip cleanly
unless staging credentials are configured — see tests/e2e/README.md. They cost
real OTP round-trips (the operator pastes the code) and mutate staging config,
always restoring it, and act only as the clearly-tagged e2e identities.

Coverage:
  a. happy-path lifecycle (request -> offered -> accept -> in_progress ->
     completed -> rating)                              [pipeline is live]
  b. density gate: remote pickup, no drivers -> no_driver_found     [UC-287]
  c. ranking: wave_size=1 -> the NEAREST driver gets the sole offer [UC-283]
  d. priority cap: a boosted FAR driver still doesn't outrank a near one [UC-284]
  e. budget give-up: short budget + no drivers -> quick no_driver_found [UC-282]
  f. ledger write: a completed ride records a RIDE_COMPLETED event  [UC-108/285]

Multi-driver ranking *math* (weights, exact ordering, cap arithmetic) is proven
deterministically by the unit suites (test_matching_eta_ranking.py,
test_matching_wave_dynamics.py, test_priority_engine.py); here we prove the same
behaviours survive end-to-end through the real API + Redis + DiddiMap.
"""

from __future__ import annotations

import pytest

from tests.e2e.helpers import E2EClient

pytestmark = pytest.mark.e2e


async def _passenger_token(client: E2EClient) -> str:
    return await client.login_via_otp(client.config.passenger_phone, role="passenger")


async def test_happy_path_ride_lifecycle(client: E2EClient) -> None:
    cfg = client.config
    passenger = await _passenger_token(client)
    driver = await client.onboard_driver(1, cfg.near_lat, cfg.near_lng, name="near")

    ride_id, offered = await client.observe_wave(
        [driver],
        lambda: client.request_ride(passenger, (cfg.pickup_lat, cfg.pickup_lng), (cfg.dropoff_lat, cfg.dropoff_lng)),
    )
    assert "near" in offered, "the only online driver should receive the offer"

    await client.accept_ride(driver, ride_id)
    # wait_for_status raises if the ride never reaches one of these.
    await client.wait_for_status(passenger, ride_id, {"matched", "driver_en_route"})
    await client.set_ride_status(driver.token, ride_id, "in_progress")
    await client.set_ride_status(driver.token, ride_id, "completed")
    assert await client.wait_for_status(passenger, ride_id, {"completed"}) == "completed"
    await client.rate_ride(passenger, ride_id, stars=5)


async def test_density_gate_no_drivers_nearby(client: E2EClient) -> None:
    cfg = client.config
    passenger = await _passenger_token(client)
    ride_id = await client.request_ride(
        passenger, (cfg.remote_lat, cfg.remote_lng), (cfg.dropoff_lat, cfg.dropoff_lng),
    )
    assert await client.wait_for_status(passenger, ride_id, {"no_driver_found"}, timeout=45) == "no_driver_found"


async def test_ranking_offers_the_nearest_driver_first(dispatch_config_guard: E2EClient) -> None:
    client = dispatch_config_guard
    cfg = client.config
    # wave_size=1 makes the first wave go to exactly the top-ranked driver.
    live = await client.get_config()
    await client.put_config({**live, "offer_wave_size": 1})

    passenger = await _passenger_token(client)
    near = await client.onboard_driver(1, cfg.near_lat, cfg.near_lng, name="near")
    far = await client.onboard_driver(2, cfg.far_lat, cfg.far_lng, name="far")

    ride_id, offered = await client.observe_wave(
        [near, far],
        lambda: client.request_ride(passenger, (cfg.pickup_lat, cfg.pickup_lng), (cfg.dropoff_lat, cfg.dropoff_lng)),
    )
    assert offered[:1] == ["near"], f"nearest driver should get the sole first-wave offer, got {offered}"


async def test_priority_cap_far_driver_cannot_outrank_near(dispatch_config_guard: E2EClient) -> None:
    client = dispatch_config_guard
    cfg = client.config
    live = await client.get_config()
    await client.put_config({**live, "offer_wave_size": 1})

    passenger = await _passenger_token(client)
    near = await client.onboard_driver(1, cfg.near_lat, cfg.near_lng, name="near")
    far = await client.onboard_driver(2, cfg.far_lat, cfg.far_lng, name="far")

    # Give the FAR driver a large, short-lived boost. The cap (UC-284) must keep
    # the NEAR driver ahead regardless.
    await client.grant_boost(far.driver_id, points=9999, duration_minutes=5, reason="e2e-cap-test")

    ride_id, offered = await client.observe_wave(
        [near, far],
        lambda: client.request_ride(passenger, (cfg.pickup_lat, cfg.pickup_lng), (cfg.dropoff_lat, cfg.dropoff_lng)),
    )
    assert offered[:1] == ["near"], f"cap should keep near driver first despite far boost, got {offered}"


async def test_search_budget_gives_up_quickly(dispatch_config_guard: E2EClient) -> None:
    client = dispatch_config_guard
    cfg = client.config
    live = await client.get_config()
    await client.put_config({**live, "search_budget_seconds": 5})

    passenger = await _passenger_token(client)
    ride_id = await client.request_ride(
        passenger, (cfg.remote_lat, cfg.remote_lng), (cfg.dropoff_lat, cfg.dropoff_lng),
    )
    # With a 5s budget and no drivers, it must fail fast rather than cycle waves.
    assert await client.wait_for_status(passenger, ride_id, {"no_driver_found"}, timeout=25) == "no_driver_found"


async def test_completed_ride_records_a_priority_ledger_event(client: E2EClient) -> None:
    cfg = client.config
    passenger = await _passenger_token(client)
    driver = await client.onboard_driver(1, cfg.near_lat, cfg.near_lng, name="near")

    ride_id, offered = await client.observe_wave(
        [driver],
        lambda: client.request_ride(passenger, (cfg.pickup_lat, cfg.pickup_lng), (cfg.dropoff_lat, cfg.dropoff_lng)),
    )
    assert "near" in offered
    await client.accept_ride(driver, ride_id)
    await client.wait_for_status(passenger, ride_id, {"matched", "driver_en_route"})
    await client.set_ride_status(driver.token, ride_id, "in_progress")
    await client.set_ride_status(driver.token, ride_id, "completed")
    await client.wait_for_status(passenger, ride_id, {"completed"})

    ledger = await client.driver_priority(driver.driver_id)
    blob = str(ledger).lower()
    assert "ride_completed" in blob or "completed" in blob, f"expected a completion event in the ledger, got {ledger}"
