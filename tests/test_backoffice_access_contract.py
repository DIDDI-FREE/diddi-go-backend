"""Backoffice access contract: human admin reads/decisions, never user elevation."""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_kyc_queue_requires_authentication(client) -> None:
    response = await client.get("/v1/drivers/kyc")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_MISSING"


@pytest.mark.asyncio
async def test_passenger_cannot_read_kyc_queue(client, passenger_headers) -> None:
    response = await client.get("/v1/drivers/kyc", headers=passenger_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"


@pytest.mark.asyncio
async def test_admin_kyc_queue_rejects_invalid_status(client, admin_headers) -> None:
    response = await client.get("/v1/drivers/kyc?status=unknown", headers=admin_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "DRIVER_KYC_STATUS_INVALID"


@pytest.mark.asyncio
async def test_admin_kyc_detail_returns_not_found_for_unknown_driver(client, admin_headers) -> None:
    response = await client.get(f"/v1/drivers/{uuid4()}/kyc", headers=admin_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DRIVER_PROFILE_NOT_FOUND"


@pytest.mark.asyncio
@pytest.mark.parametrize("suffix", ["wallet", "wallet/ledger"])
async def test_passenger_cannot_read_driver_finances(client, passenger_headers, suffix: str) -> None:
    response = await client.get(f"/v1/admin/drivers/{uuid4()}/{suffix}", headers=passenger_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"


@pytest.mark.asyncio
async def test_admin_wallet_rejects_malformed_driver_id(client, admin_headers) -> None:
    response = await client.get("/v1/admin/drivers/not-a-uuid/wallet", headers=admin_headers)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_role_query_parameter_never_elevates_passenger(client, passenger_headers) -> None:
    response = await client.get("/v1/rides?role=admin", headers=passenger_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_ROLE"
