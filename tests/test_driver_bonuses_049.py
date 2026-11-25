"""Ticket 049 point 4: the driver's bonuses, relayed from Rewards (contract 057, point 3)."""

from uuid import uuid4

import pytest

from app_base.core.errors import ApiError
from app_base.main import app
from app_base.modules.ride.application import rewards_offers as offers_module
from app_base.modules.ride.application.rewards_offers import RewardsOffersService

pytestmark = pytest.mark.unit

BONUS = {
    "offer_id": str(uuid4()), "campaign_version_id": str(uuid4()), "name": "Bonus d'accueil",
    "description": "1 000 F par course, 10 courses", "kind": "stepped", "state": "withdrawable",
    "total_amount_minor": 10000, "unlocked_amount_minor": 3000, "locked_amount_minor": 7000,
    "paying_amount_minor": 2000, "paid_amount_minor": 1000, "expired_amount_minor": 0,
    "progress": {"current": 3, "target": 10, "counts": "completed and paid rides"},
    "window_start": "account_created", "window_start_at": "2026-11-25T00:00:00Z", "deadline_at": None,
}


class FakeRewards:
    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error
        self.asked: list = []

    async def professional_bonuses(self, *, professional_id, request_id):
        self.asked.append(professional_id)
        if self.error:
            raise self.error
        return {"professional_id": str(professional_id), "service_code": "go", "bonuses": [BONUS]}


@pytest.fixture(autouse=True)
def rewards_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(offers_module.settings, "diddi_rewards_enabled", True)


@pytest.mark.asyncio
async def test_driver_bonuses_are_relayed_untouched_for_the_driver_user_id() -> None:
    rewards = FakeRewards()
    user_id = uuid4()
    result = await RewardsOffersService(rewards).driver_bonuses(user_id, request_id="r")
    assert result == {"bonuses": [BONUS]}
    assert rewards.asked == [user_id]


@pytest.mark.asyncio
async def test_rewards_failure_is_503() -> None:
    service = RewardsOffersService(FakeRewards(error=ApiError(403, "REWARDS_OPERATION_FAILED", "scope")))
    with pytest.raises(ApiError) as excinfo:
        await service.driver_bonuses(uuid4(), request_id="r")
    assert excinfo.value.status_code == 503 and excinfo.value.code == "REWARDS_UNAVAILABLE"


def test_route_answers_through_the_app_with_a_driver_profile() -> None:
    from types import SimpleNamespace

    from fastapi.testclient import TestClient

    from app_base.core.auth_deps import get_current_active_user
    from app_base.core.deps import driver_profile_repo
    from app_base.modules.ride.presentation.rewards_router import rewards_offers_service

    user = SimpleNamespace(id=uuid4())

    class Drivers:
        def __init__(self, found: bool) -> None:
            self.found = found

        async def find_by_user_id(self, user_id):
            return SimpleNamespace(id=uuid4(), user_id=user_id) if self.found else None

    app.dependency_overrides[get_current_active_user] = lambda: user
    app.dependency_overrides[rewards_offers_service] = lambda: RewardsOffersService(FakeRewards())
    try:
        app.dependency_overrides[driver_profile_repo] = lambda: Drivers(True)
        ok = TestClient(app).get("/v1/drivers/me/bonuses")
        app.dependency_overrides[driver_profile_repo] = lambda: Drivers(False)
        missing = TestClient(app).get("/v1/drivers/me/bonuses")
    finally:
        app.dependency_overrides.clear()
    assert ok.status_code == 200 and ok.json() == {"bonuses": [BONUS]}
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "DRIVER_PROFILE_NOT_FOUND"
