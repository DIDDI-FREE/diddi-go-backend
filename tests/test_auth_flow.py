"""End-to-end auth flow against the real database.

Covers API contract §1: register → OTP request → OTP verify → JWT →
/auth/me, plus refresh and the failure modes the contract specifies.
"""

from __future__ import annotations

import pytest


async def register_and_login(client, otp_code, phone: str, role: str = "passenger") -> str:
    """Helper — full signup flow, returns the access token."""
    r = await client.post(
        "/v1/auth/register",
        json={"phone": phone, "full_name": "Test User", "role": role},
    )
    assert r.status_code == 201, r.text

    r = await client.post("/v1/auth/otp/request", json={"phone": phone})
    assert r.status_code == 200, r.text

    r = await client.post(
        "/v1/auth/otp/verify",
        json={"phone": phone, "code": otp_code.latest()},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def test_register_returns_pending_verification(client, phone_factory) -> None:
    phone = phone_factory()
    r = await client.post(
        "/v1/auth/register",
        json={"phone": phone, "full_name": "Awa Kone", "role": "passenger"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["phone"] == phone
    assert body["status"] == "pending_verification"
    assert "user_id" in body


async def test_register_duplicate_phone_conflicts(client, phone_factory) -> None:
    phone = phone_factory()
    payload = {"phone": phone, "full_name": "Awa Kone", "role": "passenger"}

    assert (await client.post("/v1/auth/register", json=payload)).status_code == 201

    r = await client.post("/v1/auth/register", json=payload)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "PHONE_ALREADY_REGISTERED"


async def test_register_rejects_unknown_role(client, phone_factory) -> None:
    r = await client.post(
        "/v1/auth/register",
        json={"phone": phone_factory(), "full_name": "X", "role": "wizard"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_ROLE"


@pytest.mark.parametrize(
    "phone",
    [
        pytest.param("+22507000ZZZ1", id="letters"),
        pytest.param("0700000000", id="no-country-code"),
        pytest.param("+225", id="country-code-only"),
        pytest.param("+0700000000", id="leading-zero-country"),
        pytest.param("", id="empty"),
        pytest.param("+225070000000000000000", id="too-long"),
        pytest.param("not a phone", id="free-text"),
    ],
)
async def test_register_rejects_malformed_phone_numbers(client, phone) -> None:
    r = await client.post(
        "/v1/auth/register",
        json={"phone": phone, "full_name": "X", "role": "passenger"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_PHONE_FORMAT"


async def test_register_normalises_spaces_in_phone(client) -> None:
    """`+225 07 12 34 56 78` and `+2250712345678` are the same subscriber."""
    spaced = "+225 07 12 34 56 78"
    r = await client.post(
        "/v1/auth/register",
        json={"phone": spaced, "full_name": "Awa Kone", "role": "passenger"},
    )
    assert r.status_code == 201
    assert r.json()["phone"] == "+2250712345678"

    # The normalised form must collide with the spaced one.
    r = await client.post(
        "/v1/auth/register",
        json={"phone": "+2250712345678", "full_name": "Awa Kone", "role": "passenger"},
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "PHONE_ALREADY_REGISTERED"


async def test_otp_request_rejects_a_malformed_phone(client) -> None:
    r = await client.post("/v1/auth/otp/request", json={"phone": "abc"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "INVALID_PHONE_FORMAT"


async def test_otp_verify_issues_jwt_and_activates_user(client, otp_code, phone_factory) -> None:
    phone = phone_factory()
    await client.post(
        "/v1/auth/register",
        json={"phone": phone, "full_name": "Awa Kone", "role": "passenger"},
    )
    await client.post("/v1/auth/otp/request", json={"phone": phone})

    r = await client.post(
        "/v1/auth/otp/verify", json={"phone": phone, "code": otp_code.latest()},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["status"] == "active"
    assert body["user"]["role"] == "passenger"
    # JWT, not an opaque digest: three base64 segments.
    assert body["access_token"].count(".") == 2


async def test_otp_verify_rejects_wrong_code(client, phone_factory) -> None:
    phone = phone_factory()
    await client.post(
        "/v1/auth/register",
        json={"phone": phone, "full_name": "Awa Kone", "role": "passenger"},
    )
    await client.post("/v1/auth/otp/request", json={"phone": phone})

    r = await client.post("/v1/auth/otp/verify", json={"phone": phone, "code": "000000"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "OTP_INVALID"


async def test_otp_cannot_be_reused(client, otp_code, phone_factory) -> None:
    phone = phone_factory()
    await client.post(
        "/v1/auth/register",
        json={"phone": phone, "full_name": "Awa Kone", "role": "passenger"},
    )
    await client.post("/v1/auth/otp/request", json={"phone": phone})
    code = otp_code.latest()

    assert (
        await client.post("/v1/auth/otp/verify", json={"phone": phone, "code": code})
    ).status_code == 200

    r = await client.post("/v1/auth/otp/verify", json={"phone": phone, "code": code})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "OTP_INVALID"


async def test_me_requires_authentication(client) -> None:
    r = await client.get("/v1/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "TOKEN_MISSING"


async def test_me_rejects_garbage_token(client) -> None:
    r = await client.get("/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "TOKEN_INVALID"


async def test_me_returns_the_token_owner(client, otp_code, phone_factory) -> None:
    """Regression guard: /auth/me used to return the first user in a dict,
    ignoring the token entirely. It must reflect the caller's identity."""
    phone_a = phone_factory()
    phone_b = phone_factory()
    await register_and_login(client, otp_code, phone_a)
    token_b = await register_and_login(client, otp_code, phone_b, role="driver")

    r = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 200
    body = r.json()
    assert body["phone"] == phone_b
    assert body["role"] == "driver"


async def test_refresh_returns_a_new_token_pair(client, otp_code, phone_factory) -> None:
    phone = phone_factory()
    await client.post(
        "/v1/auth/register",
        json={"phone": phone, "full_name": "Awa Kone", "role": "passenger"},
    )
    await client.post("/v1/auth/otp/request", json={"phone": phone})
    tokens = (
        await client.post(
            "/v1/auth/otp/verify", json={"phone": phone, "code": otp_code.latest()},
        )
    ).json()

    r = await client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    assert r.json()["access_token"] and r.json()["refresh_token"]


async def test_refresh_rejects_an_access_token(client, otp_code, phone_factory) -> None:
    """Access and refresh tokens carry a `typ` claim; swapping them must fail."""
    phone = phone_factory()
    token = await register_and_login(client, otp_code, phone)

    r = await client.post("/v1/auth/refresh", json={"refresh_token": token})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "TOKEN_INVALID"


async def test_token_works_immediately_after_verify(client, otp_code, phone_factory) -> None:
    """Regression: a token had to be usable on the very next request.

    Writes used to be committed only when FastAPI tore the request's session
    down — which happens *after* the response is sent. A client that used its
    fresh token straight away raced that commit and was rejected with
    `403 USER_SUSPENDED`, because the account still read as
    `pending_verification`. The use case now commits before returning.
    """
    phone = phone_factory()
    await client.post(
        "/v1/auth/register",
        json={"phone": phone, "full_name": "Awa Kone", "role": "passenger"},
    )
    await client.post("/v1/auth/otp/request", json={"phone": phone})
    token = (
        await client.post(
            "/v1/auth/otp/verify", json={"phone": phone, "code": otp_code.latest()},
        )
    ).json()["access_token"]

    # No delay, no intervening request — exactly the shape that used to fail.
    r = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "active"


async def test_several_users_can_sign_up_back_to_back(client, otp_code, phone_factory) -> None:
    """Regression: the same race made the failure depend on how many accounts
    had been created on the connection, so signups worked in isolation but
    broke in sequence."""
    for _ in range(3):
        token = await register_and_login(client, otp_code, phone_factory(), role="driver")
        r = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "driver"
