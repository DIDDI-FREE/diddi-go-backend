"""End-to-end ride + payment lifecycle against the real database.

Covers API contract §2 and §3: pricing estimate, ride creation, the driver
status transitions, cancellation, rating, and cash confirmation — including
the PostGIS round-trip of pickup/dropoff geography columns.
"""

from __future__ import annotations

import pytest

from tests.test_auth_flow import register_and_login

RIDE_BODY = {
    "pickup": {"lat": 5.3599, "lng": -4.0083, "address": "Carrefour Anador, Yopougon"},
    "dropoff": {"lat": 5.3167, "lng": -4.0333, "address": "Plateau, Rue du Commerce"},
    "vehicle_category": "standard",
}


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_ride(client, passenger) -> str:
    r = await client.post("/v1/rides", json={**RIDE_BODY, "scheduled_at": None}, headers=passenger)
    assert r.status_code == 201, r.text
    return r.json()["ride_id"]


async def matched_ride(client, passenger, driver) -> str:
    """Create a ride and have the offered driver accept it."""
    ride_id = await create_ride(client, passenger)
    r = await client.post(f"/v1/rides/{ride_id}/accept", headers=driver)
    assert r.status_code == 200, f"accept: {r.text}"
    return ride_id


async def complete_ride(client, passenger, driver) -> tuple[str, int]:
    """Drive a ride all the way to `completed`. Returns (ride_id, final_fare)."""
    ride_id = await matched_ride(client, passenger, driver)
    for status in ("driver_en_route", "in_progress", "completed"):
        r = await client.patch(
            f"/v1/rides/{ride_id}/status", json={"status": status}, headers=driver,
        )
        assert r.status_code == 200, f"{status}: {r.text}"
    fare = (await client.get(f"/v1/rides/{ride_id}", headers=passenger)).json()["final_fare"]
    return ride_id, fare


# --- pricing ---------------------------------------------------------------

async def test_pricing_estimate_matches_contract_shape(client, passenger) -> None:
    r = await client.post("/v1/rides/pricing/estimate", json=RIDE_BODY, headers=passenger)
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {
        "estimated_fare", "currency", "distance_km", "duration_seconds", "surge_multiplier",
    }
    assert body["currency"] == "XOF"
    assert isinstance(body["estimated_fare"], int) and body["estimated_fare"] > 0
    assert body["distance_km"] > 0
    assert body["surge_multiplier"] == 1.0


async def test_pricing_rejects_unknown_vehicle_category(client, passenger) -> None:
    r = await client.post(
        "/v1/rides/pricing/estimate",
        json={**RIDE_BODY, "vehicle_category": "helicopter"},
        headers=passenger,
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_VEHICLE_CATEGORY"


# --- creation --------------------------------------------------------------

async def test_create_ride_returns_requested(client, passenger) -> None:
    r = await client.post("/v1/rides", json={**RIDE_BODY, "scheduled_at": None}, headers=passenger)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "requested"
    assert body["currency"] == "XOF"
    assert body["estimated_fare"] > 0
    assert body["requested_at"].endswith("Z")


async def test_create_ride_requires_authentication(client) -> None:
    r = await client.post("/v1/rides", json={**RIDE_BODY, "scheduled_at": None})
    assert r.status_code == 401


async def test_passenger_cannot_have_two_active_rides(client, passenger, driver) -> None:
    """The guard covers rides that are genuinely live. `driver` is online, so
    the first ride stays in an active state rather than dying immediately."""
    await create_ride(client, passenger)
    r = await client.post("/v1/rides", json={**RIDE_BODY, "scheduled_at": None}, headers=passenger)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ACTIVE_RIDE_ALREADY_EXISTS"


async def test_passenger_may_retry_after_no_driver_found(client, passenger) -> None:
    """With nobody online the ride ends at `no_driver_found`, which is
    terminal — it must not block the passenger from trying again."""
    first = await create_ride(client, passenger)
    detail = (await client.get(f"/v1/rides/{first}", headers=passenger)).json()
    assert detail["status"] == "no_driver_found"

    r = await client.post("/v1/rides", json={**RIDE_BODY, "scheduled_at": None}, headers=passenger)
    assert r.status_code == 201, r.text


async def test_geography_columns_round_trip(client, passenger) -> None:
    """PostGIS GEOGRAPHY(POINT,4326) must survive the write/read cycle."""
    ride_id = await create_ride(client, passenger)
    body = (await client.get(f"/v1/rides/{ride_id}", headers=passenger)).json()

    assert body["pickup"]["lat"] == pytest.approx(RIDE_BODY["pickup"]["lat"], abs=1e-6)
    assert body["pickup"]["lng"] == pytest.approx(RIDE_BODY["pickup"]["lng"], abs=1e-6)
    assert body["dropoff"]["lat"] == pytest.approx(RIDE_BODY["dropoff"]["lat"], abs=1e-6)
    assert body["dropoff"]["lng"] == pytest.approx(RIDE_BODY["dropoff"]["lng"], abs=1e-6)
    assert body["pickup"]["address"] == RIDE_BODY["pickup"]["address"]


async def test_get_ride_404_for_unknown_id(client, passenger) -> None:
    r = await client.get("/v1/rides/00000000-0000-0000-0000-000000000000", headers=passenger)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "RIDE_NOT_FOUND"


# --- status transitions ----------------------------------------------------

async def test_driver_walks_the_ride_to_completion(client, passenger, driver) -> None:
    ride_id = await matched_ride(client, passenger, driver)

    for status in ("driver_en_route", "in_progress", "completed"):
        r = await client.patch(
            f"/v1/rides/{ride_id}/status", json={"status": status}, headers=driver,
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == status

    final = (await client.get(f"/v1/rides/{ride_id}", headers=passenger)).json()
    assert final["matched_at"] and final["started_at"] and final["completed_at"]
    assert final["final_fare"] == final["estimated_fare"]


async def test_illegal_transition_is_rejected(client, passenger, driver) -> None:
    ride_id = await matched_ride(client, passenger, driver)
    r = await client.patch(
        f"/v1/rides/{ride_id}/status", json={"status": "completed"}, headers=driver,
    )
    assert r.status_code == 409
    body = r.json()["error"]
    assert body["code"] == "INVALID_STATUS_TRANSITION"
    assert body["details"]["current_status"] == "matched"
    assert body["details"]["attempted_status"] == "completed"
    assert body["details"]["request_id"]


async def test_passenger_cannot_change_status(client, passenger, driver) -> None:
    ride_id = await matched_ride(client, passenger, driver)
    r = await client.patch(
        f"/v1/rides/{ride_id}/status", json={"status": "driver_en_route"}, headers=passenger,
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "DRIVER_PROFILE_NOT_FOUND"


# --- cancellation ----------------------------------------------------------

async def test_cancel_sets_cancelled_by_passenger(client, passenger, driver) -> None:
    ride_id = await create_ride(client, passenger)
    r = await client.post(
        f"/v1/rides/{ride_id}/cancel",
        json={"reason": "passenger_changed_mind"},
        headers=passenger,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled_by_passenger"
    assert r.json()["cancelled_at"].endswith("Z")


async def test_cancel_rejects_unknown_reason(client, passenger, driver) -> None:
    ride_id = await create_ride(client, passenger)
    r = await client.post(
        f"/v1/rides/{ride_id}/cancel", json={"reason": "bad_weather"}, headers=passenger,
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_CANCEL_REASON"


async def test_cannot_cancel_a_ride_that_found_no_driver(client, passenger) -> None:
    """`no_driver_found` is terminal. Cancelling it used to raise out of the
    domain entity and surface as a 500."""
    ride_id = await create_ride(client, passenger)
    r = await client.post(
        f"/v1/rides/{ride_id}/cancel",
        json={"reason": "passenger_changed_mind"},
        headers=passenger,
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "RIDE_NOT_CANCELLABLE"


async def test_cannot_cancel_a_completed_ride(client, passenger, driver) -> None:
    ride_id, _ = await complete_ride(client, passenger, driver)
    r = await client.post(
        f"/v1/rides/{ride_id}/cancel",
        json={"reason": "passenger_changed_mind"},
        headers=passenger,
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "RIDE_ALREADY_COMPLETED"


# --- listing ---------------------------------------------------------------

async def test_list_rides_is_paginated(client, passenger) -> None:
    await create_ride(client, passenger)
    r = await client.get("/v1/rides", headers=passenger)
    assert r.status_code == 200
    body = r.json()
    assert set(body["pagination"]) == {"page", "page_size", "total_items", "total_pages"}
    assert body["pagination"]["total_items"] >= 1
    assert set(body["data"][0]) == {
        "id", "status", "final_fare", "completed_at", "pickup_address", "dropoff_address",
    }


async def test_list_rides_is_scoped_to_the_caller(client, passenger, otp_code, phone_factory) -> None:
    await create_ride(client, passenger)
    other = auth(await register_and_login(client, otp_code, phone_factory("+22509")))

    r = await client.get("/v1/rides", headers=other)
    assert r.status_code == 200
    assert r.json()["pagination"]["total_items"] == 0


# --- ratings ---------------------------------------------------------------

async def test_rating_is_accepted_once_per_role(client, passenger, driver) -> None:
    ride_id, _ = await complete_ride(client, passenger, driver)

    r = await client.post(
        f"/v1/rides/{ride_id}/rating",
        json={"rating": 5, "comment": "Trajet rapide"},
        headers=passenger,
    )
    assert r.status_code == 201
    assert r.json()["rating"] == 5

    r = await client.post(f"/v1/rides/{ride_id}/rating", json={"rating": 4}, headers=passenger)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "RATING_ALREADY_SUBMITTED"

    # The driver still gets their own slot — UNIQUE(ride_id, rater_role).
    r = await client.post(f"/v1/rides/{ride_id}/rating", json={"rating": 4}, headers=driver)
    assert r.status_code == 201


async def test_rating_out_of_range_is_rejected(client, passenger, driver) -> None:
    ride_id, _ = await complete_ride(client, passenger, driver)
    r = await client.post(f"/v1/rides/{ride_id}/rating", json={"rating": 9}, headers=passenger)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "RATING_OUT_OF_RANGE"


# --- payment ---------------------------------------------------------------

async def test_payment_starts_pending(client, passenger, driver) -> None:
    ride_id, _ = await complete_ride(client, passenger, driver)
    r = await client.get(f"/v1/payments/{ride_id}", headers=passenger)
    assert r.status_code == 200
    assert r.json()["status"] == "pending"
    assert r.json()["method"] == "cash"


async def test_driver_confirms_cash_collection(client, passenger, driver) -> None:
    ride_id, fare = await complete_ride(client, passenger, driver)

    r = await client.post(
        f"/v1/payments/{ride_id}/confirm-cash",
        json={"amount_collected": fare},
        headers=driver,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "collected"
    assert body["amount"] == fare
    assert body["currency"] == "XOF"

    after = await client.get(f"/v1/payments/{ride_id}", headers=passenger)
    assert after.json()["status"] == "collected"


async def test_confirm_cash_rejects_wildly_wrong_amount(client, passenger, driver) -> None:
    ride_id, fare = await complete_ride(client, passenger, driver)
    r = await client.post(
        f"/v1/payments/{ride_id}/confirm-cash",
        json={"amount_collected": fare * 10},
        headers=driver,
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "AMOUNT_MISMATCH"


async def test_confirm_cash_before_completion_is_rejected(client, passenger, driver) -> None:
    ride_id = await create_ride(client, passenger)
    r = await client.post(
        f"/v1/payments/{ride_id}/confirm-cash", json={"amount_collected": 2500}, headers=driver,
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "RIDE_NOT_COMPLETED"


async def test_passenger_cannot_confirm_cash(client, passenger, driver) -> None:
    ride_id, fare = await complete_ride(client, passenger, driver)
    r = await client.post(
        f"/v1/payments/{ride_id}/confirm-cash",
        json={"amount_collected": fare},
        headers=passenger,
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "DRIVER_PROFILE_NOT_FOUND"
