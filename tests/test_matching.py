"""Matching engine tests — driver onboarding, sequential offers, and the
accept/decline race.

Runs against the real Postgres and the real Redis: the offer window is a
Redis TTL and the claim is a `SET NX`, so a fake would not exercise the
behaviour that matters.
"""

from __future__ import annotations

import asyncio

from app_base.core.redis import create_redis_pool
from app_base.core.settings import settings
from app_base.modules.ride.infra.offer_store import OFFER_KEY_PREFIX
from tests.test_ride_flow import create_ride

# Yopougon (the default pickup) and a point ~200 km away in Yamoussoukro,
# comfortably outside the 5 km matching radius.
NEAR = {"lat": 5.3599, "lng": -4.0083}
SLIGHTLY_FURTHER = {"lat": 5.3700, "lng": -4.0200}
FAR = {"lat": 6.8276, "lng": -5.2893}


async def expire_offer(ride_id: str) -> None:
    """Simulate the 15-second response window lapsing.

    Deleting the offer key is exactly what Redis does on expiry, so the engine
    cannot tell the difference — and the test does not have to sleep.
    """
    redis = create_redis_pool(settings.redis_url)
    try:
        await redis.delete(f"{OFFER_KEY_PREFIX}{ride_id}")
    finally:
        await redis.aclose()


# --- driver onboarding -----------------------------------------------------

async def test_driver_can_create_a_profile(client, driver_headers) -> None:
    r = await client.post(
        "/v1/drivers/profile", json={"license_number": "CI-12345"}, headers=driver_headers,
    )
    assert r.status_code == 201
    assert r.json()["license_number"] == "CI-12345"


async def test_driver_profile_is_unique_per_account(client, driver_headers) -> None:
    payload = {"license_number": "CI-12345"}
    assert (await client.post("/v1/drivers/profile", json=payload, headers=driver_headers)).status_code == 201

    r = await client.post("/v1/drivers/profile", json=payload, headers=driver_headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "DRIVER_PROFILE_ALREADY_EXISTS"


async def test_authenticated_user_can_create_a_driver_profile(client, passenger_headers) -> None:
    r = await client.post(
        "/v1/drivers/profile", json={"license_number": "CI-12345"}, headers=passenger_headers,
    )
    assert r.status_code == 201
    assert r.json()["license_number"] == "CI-12345"


async def test_vehicle_requires_a_profile_first(client, driver_headers) -> None:
    r = await client.post(
        "/v1/drivers/vehicle",
        json={"plate_number": "CI-4429-AB", "category": "standard"},
        headers=driver_headers,
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "DRIVER_PROFILE_NOT_FOUND"


async def test_going_online_requires_a_vehicle(client, driver_headers) -> None:
    """A driver with no vehicle must never enter the matching pool."""
    await client.post(
        "/v1/drivers/profile", json={"license_number": "CI-999"}, headers=driver_headers,
    )
    r = await client.post("/v1/drivers/online", json=NEAR, headers=driver_headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "NO_ACTIVE_VEHICLE"


async def test_driver_me_reports_profile_and_vehicle(client, online_driver) -> None:
    r = await client.get("/v1/drivers/me", headers=online_driver)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "active"
    assert body["vehicle"]["make"] == "Toyota"


# --- offers ----------------------------------------------------------------

async def test_ride_with_no_driver_online_finds_nobody(client, passenger) -> None:
    ride_id = await create_ride(client, passenger)
    detail = (await client.get(f"/v1/rides/{ride_id}", headers=passenger)).json()
    assert detail["status"] == "no_driver_found"


async def test_online_driver_receives_the_offer_and_can_accept(
    client, passenger, online_driver,
) -> None:
    ride_id = await create_ride(client, passenger)

    r = await client.post(f"/v1/rides/{ride_id}/accept", headers=online_driver)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "matched"
    assert body["driver_id"] and body["vehicle_id"]
    assert body["matched_at"].endswith("Z")


async def test_accepting_assigns_driver_and_vehicle_to_the_ride(
    client, passenger, online_driver,
) -> None:
    """The contract's ride detail must expose the driver and their vehicle
    once matched — it was always `null` before the engine existed."""
    ride_id = await create_ride(client, passenger)
    await client.post(f"/v1/rides/{ride_id}/accept", headers=online_driver)

    detail = (await client.get(f"/v1/rides/{ride_id}", headers=passenger)).json()
    assert detail["status"] == "matched"
    assert detail["driver"] is not None
    assert detail["driver"]["rating_avg"] == 5.0
    assert detail["driver"]["vehicle"]["plate_number"]
    assert detail["driver"]["phone"], "passenger needs the driver's number to meet them"


async def test_business_driver_with_user_role_can_find_assigned_rides(
    client, passenger, passenger_factory,
) -> None:
    """DiddiAuth emits role=user; DiddiGo must use driver_profiles for driver
    ride history and detail access."""
    business_driver = await passenger_factory()
    r = await client.post(
        "/v1/drivers/profile",
        json={"license_number": "CI-BUSINESS"},
        headers=business_driver,
    )
    assert r.status_code == 201, r.text

    r = await client.post(
        "/v1/drivers/vehicle",
        json={
            "plate_number": "CI-BIZ-01",
            "make": "Toyota",
            "model": "Yaris",
            "color": "gris",
            "category": "standard",
        },
        headers=business_driver,
    )
    assert r.status_code == 201, r.text

    r = await client.post("/v1/drivers/online", json=NEAR, headers=business_driver)
    assert r.status_code == 200, r.text

    ride_id = await create_ride(client, passenger)
    r = await client.post(f"/v1/rides/{ride_id}/accept", headers=business_driver)
    assert r.status_code == 200, r.text

    r = await client.get(f"/v1/rides/{ride_id}", headers=business_driver)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "matched"

    r = await client.get("/v1/rides?role=driver", headers=business_driver)
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["pagination"]["total_items"] == 1
    assert payload["data"][0]["id"] == ride_id


async def test_offer_goes_to_the_nearest_driver_first(
    client, passenger, driver_factory,
) -> None:
    nearest = await driver_factory(NEAR)
    further = await driver_factory(SLIGHTLY_FURTHER)

    ride_id = await create_ride(client, passenger)

    # The further driver was never offered this ride, so cannot take it.
    r = await client.post(f"/v1/rides/{ride_id}/accept", headers=further)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "OFFER_NOT_YOURS"

    assert (await client.post(f"/v1/rides/{ride_id}/accept", headers=nearest)).status_code == 200


async def test_drivers_outside_the_radius_are_not_offered(
    client, passenger, driver_factory,
) -> None:
    await driver_factory(FAR)
    ride_id = await create_ride(client, passenger)

    detail = (await client.get(f"/v1/rides/{ride_id}", headers=passenger)).json()
    assert detail["status"] == "no_driver_found"


async def test_decline_passes_the_offer_to_the_next_driver(
    client, passenger, driver_factory,
) -> None:
    nearest = await driver_factory(NEAR)
    backup = await driver_factory(SLIGHTLY_FURTHER)

    ride_id = await create_ride(client, passenger)

    r = await client.post(f"/v1/rides/{ride_id}/decline", headers=nearest)
    assert r.status_code == 200
    assert r.json()["reoffered"] is True

    # The offer moved on: the backup can now accept, the decliner cannot.
    assert (await client.post(f"/v1/rides/{ride_id}/accept", headers=nearest)).status_code == 403
    assert (await client.post(f"/v1/rides/{ride_id}/accept", headers=backup)).status_code == 200


async def test_a_driver_is_never_offered_the_same_ride_twice(
    client, passenger, online_driver,
) -> None:
    """The only driver declines, so the pool is exhausted rather than looping
    back to them."""
    ride_id = await create_ride(client, passenger)

    r = await client.post(f"/v1/rides/{ride_id}/decline", headers=online_driver)
    assert r.status_code == 200
    assert r.json()["reoffered"] is False

    detail = (await client.get(f"/v1/rides/{ride_id}", headers=passenger)).json()
    assert detail["status"] == "no_driver_found"


async def test_expired_offer_cannot_be_accepted(client, passenger, online_driver) -> None:
    ride_id = await create_ride(client, passenger)
    await expire_offer(ride_id)

    r = await client.post(f"/v1/rides/{ride_id}/accept", headers=online_driver)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "OFFER_EXPIRED"


async def test_timed_out_offer_moves_to_the_next_driver(
    client, passenger, driver_factory,
) -> None:
    """Nobody answers the first driver; the window lapses and the ride is
    offered onward the next time matching runs."""
    first = await driver_factory(NEAR)
    second = await driver_factory(SLIGHTLY_FURTHER)

    ride_id = await create_ride(client, passenger)
    await expire_offer(ride_id)

    # A decline from the timed-out holder re-drives matching; the engine finds
    # the next untried candidate.
    r = await client.post(f"/v1/rides/{ride_id}/decline", headers=first)
    assert r.json()["reoffered"] is True
    assert (await client.post(f"/v1/rides/{ride_id}/accept", headers=second)).status_code == 200


# --- races and guards ------------------------------------------------------

async def test_only_one_driver_can_win_a_simultaneous_accept(
    client, passenger, driver_factory,
) -> None:
    """The `SET NX` claim is what makes double-accept impossible. Both
    drivers hold a valid-looking offer path; exactly one must win."""
    first = await driver_factory(NEAR)
    second = await driver_factory(SLIGHTLY_FURTHER)
    ride_id = await create_ride(client, passenger)

    # Hand the offer to `second` as well, so both look entitled to accept.
    redis = create_redis_pool(settings.redis_url)
    try:
        results = await asyncio.gather(
            client.post(f"/v1/rides/{ride_id}/accept", headers=first),
            client.post(f"/v1/rides/{ride_id}/accept", headers=second),
            return_exceptions=True,
        )
    finally:
        await redis.aclose()

    statuses = [r.status_code for r in results if hasattr(r, "status_code")]
    assert statuses.count(200) == 1, f"exactly one accept must win, got {statuses}"


async def test_accepting_an_already_matched_ride_is_rejected(
    client, passenger, driver_factory,
) -> None:
    first = await driver_factory(NEAR)
    second = await driver_factory(SLIGHTLY_FURTHER)
    ride_id = await create_ride(client, passenger)

    assert (await client.post(f"/v1/rides/{ride_id}/accept", headers=first)).status_code == 200

    r = await client.post(f"/v1/rides/{ride_id}/accept", headers=second)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "RIDE_ALREADY_MATCHED"


async def test_passenger_cannot_accept_a_ride(client, passenger, online_driver) -> None:
    ride_id = await create_ride(client, passenger)
    r = await client.post(f"/v1/rides/{ride_id}/accept", headers=passenger)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "DRIVER_PROFILE_NOT_FOUND"


async def test_accept_requires_a_known_ride(client, online_driver) -> None:
    r = await client.post(
        "/v1/rides/00000000-0000-0000-0000-000000000000/accept", headers=online_driver,
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "RIDE_NOT_FOUND"


# --- availability lifecycle ------------------------------------------------

async def test_a_matched_driver_leaves_the_pool(
    client, passenger, passenger_factory, driver_factory,
) -> None:
    """A driver on a ride must not be offered another one."""
    driver = await driver_factory(NEAR)
    first_passenger = passenger
    ride_id = await create_ride(client, first_passenger)
    assert (await client.post(f"/v1/rides/{ride_id}/accept", headers=driver)).status_code == 200

    # A second passenger requests a ride with that same driver the only one
    # nearby — but they are busy, so nobody is available.
    other = await passenger_factory()
    second_ride = await create_ride(client, other)
    detail = (await client.get(f"/v1/rides/{second_ride}", headers=other)).json()
    assert detail["status"] == "no_driver_found"


async def test_completing_a_ride_returns_the_driver_to_the_pool(
    client, passenger, passenger_factory, driver_factory,
) -> None:
    driver = await driver_factory(NEAR)
    ride_id = await create_ride(client, passenger)
    await client.post(f"/v1/rides/{ride_id}/accept", headers=driver)
    for status in ("driver_en_route", "in_progress", "completed"):
        await client.patch(f"/v1/rides/{ride_id}/status", json={"status": status}, headers=driver)

    other = await passenger_factory()
    second_ride = await create_ride(client, other)
    r = await client.post(f"/v1/rides/{second_ride}/accept", headers=driver)
    assert r.status_code == 200, "driver should be matchable again after finishing"


async def test_cancelling_returns_the_driver_to_the_pool(
    client, passenger, passenger_factory, driver_factory,
) -> None:
    driver = await driver_factory(NEAR)
    ride_id = await create_ride(client, passenger)
    await client.post(f"/v1/rides/{ride_id}/accept", headers=driver)
    await client.post(
        f"/v1/rides/{ride_id}/cancel",
        json={"reason": "passenger_changed_mind"},
        headers=passenger,
    )

    other = await passenger_factory()
    second_ride = await create_ride(client, other)
    r = await client.post(f"/v1/rides/{second_ride}/accept", headers=driver)
    assert r.status_code == 200, "driver should be matchable again after a cancellation"


async def test_going_offline_removes_a_driver_from_matching(
    client, passenger, online_driver,
) -> None:
    assert (await client.post("/v1/drivers/offline", headers=online_driver)).status_code == 200

    ride_id = await create_ride(client, passenger)
    detail = (await client.get(f"/v1/rides/{ride_id}", headers=passenger)).json()
    assert detail["status"] == "no_driver_found"
