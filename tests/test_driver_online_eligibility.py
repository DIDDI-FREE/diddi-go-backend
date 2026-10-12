from __future__ import annotations

from uuid import uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.modules.ride.application.driver_online_eligibility import DriverOnlineEligibilityService

pytestmark = pytest.mark.unit


class FakeWallets:
    def __init__(self, *, balance: int, minimum: int) -> None:
        self.balance = balance
        self.minimum = minimum

    async def get_online_eligibility(self, driver_id):
        return {
            "eligible": self.balance >= self.minimum,
            "balance": self.balance,
            "min_balance": self.minimum,
            "currency": "XOF",
        }


class FakePartners:
    def __init__(self, *, blocked: bool = False) -> None:
        self.blocked = blocked

    async def driver_is_blocked_by_partner(self, driver_id):
        return self.blocked, "partner_not_active:suspended" if self.blocked else None


@pytest.mark.asyncio
async def test_online_eligibility_exposes_low_balance_as_capability_blocker() -> None:
    service = DriverOnlineEligibilityService(
        wallets=FakeWallets(balance=1_000, minimum=5_000),  # type: ignore[arg-type]
        partners=FakePartners(),  # type: ignore[arg-type]
    )

    result = await service.evaluate(uuid4())

    assert result["eligible"] is False
    assert result["blocking_reasons"] == ["driver_balance_too_low"]
    assert result["wallet"] == {
        "eligible": False,
        "balance": 1_000,
        "min_balance": 5_000,
        "currency": "XOF",
    }
    with pytest.raises(ApiError) as exc_info:
        await service.ensure_can_go_online(uuid4())
    assert exc_info.value.code == "DRIVER_BALANCE_TOO_LOW"


@pytest.mark.asyncio
async def test_online_eligibility_prioritises_partner_block() -> None:
    service = DriverOnlineEligibilityService(
        wallets=FakeWallets(balance=10_000, minimum=5_000),  # type: ignore[arg-type]
        partners=FakePartners(blocked=True),  # type: ignore[arg-type]
    )

    result = await service.evaluate(uuid4())

    assert result["eligible"] is False
    assert result["blocking_reasons"] == ["partner_suspended"]
    with pytest.raises(ApiError) as exc_info:
        await service.ensure_can_go_online(uuid4())
    assert exc_info.value.code == "PARTNER_SUSPENDED"
