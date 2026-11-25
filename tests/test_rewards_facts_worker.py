"""Facts protocol worker on real Postgres (tickets 049, 066, 069).

A fact waits in the outbox until Rewards accepts it. A `credit_professional` action writes one
`rewards_bonus` line in the driver's wallet, once, then is confirmed with that line's id.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app_base.core.database import async_session_factory, engine
from app_base.core.errors import ApiError
from app_base.modules.auth.infra.models import UserModel
from app_base.modules.payment.application import rewards_events
from app_base.modules.payment.infra import models as payment_orm
from app_base.modules.payment.infra.repositories import SqlAlchemyPaymentRepository
from app_base.modules.ride.infra import models as ride_orm


class FakeRewards:
    configured = True

    def __init__(self, *, actions=None, error: ApiError | None = None) -> None:
        self.actions = actions or []
        self.error = error
        self.facts: list[dict] = []
        self.done: list[dict] = []

    async def report_fact(self, *, fact, request_id):
        self.facts.append(fact)
        if self.error is not None:
            raise self.error
        return {"fact_id": fact["fact_id"], "status": "accepted", "actions": self.actions}

    async def pending_actions(self, *, request_id):
        return {"actions": self.actions}

    async def action_done(self, **kwargs):
        self.done.append(kwargs)
        return {"action_id": str(kwargs["action_id"]), "state": "done"}


async def _driver() -> tuple:
    user_id, driver_id = uuid4(), uuid4()
    async with async_session_factory() as session:
        session.add(UserModel(id=user_id, phone=f"+225{user_id.int % 10_000_000_000:010d}", role="user"))
        await session.flush()
        session.add(
            ride_orm.DriverProfileModel(
                id=driver_id, user_id=user_id, license_number=f"LIC-{driver_id.hex[:12]}", status="active"
            )
        )
        await session.commit()
    return user_id, driver_id


async def _queue_fact(ride_id) -> str:
    fact = {
        "schema_version": "1", "fact_id": f"diddigo:order.paid:{ride_id}", "type": "order.paid",
        "order_id": str(ride_id), "customer_id": str(uuid4()), "occurred_at": "2026-11-25T10:00:00Z",
        "amount_minor": 1234, "discount_minor": 0, "currency": "XOF", "payment_method": "cash",
        "professional_id": None, "parent": None, "rewards_reservation_id": None,
    }
    async with async_session_factory() as session:
        await SqlAlchemyPaymentRepository(session).enqueue_rewards_event(
            event_type="order.paid", ride_id=ride_id, payload=fact
        )
        await session.commit()
    return fact["fact_id"]


async def _outbox_row(fact_id: str):
    async with async_session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(payment_orm.RewardsEventOutboxModel).where(payment_orm.RewardsEventOutboxModel.event_id == fact_id)
        )
        return result.scalar_one()


@pytest.fixture(autouse=True)
def rewards_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rewards_events.settings, "diddi_rewards_enabled", True)


@pytest.mark.asyncio
async def test_fact_is_sent_and_bonus_credited_once_then_confirmed() -> None:
    user_id, driver_id = await _driver()
    action_id = uuid4()
    action = {
        "type": "credit_professional", "action_id": str(action_id), "professional_id": str(user_id),
        "amount_minor": 1000, "currency": "XOF", "offer_id": str(uuid4()), "offer_name": "Bonus d'accueil",
    }
    rewards = FakeRewards(actions=[action])
    fact_id = await _queue_fact(uuid4())

    await rewards_events.run_rewards_facts_once(rewards, limit=500)
    # The same action again (pending list, or a duplicate answer): no second credit.
    await rewards_events.run_rewards_actions_once(rewards)

    assert fact_id in {fact["fact_id"] for fact in rewards.facts}
    assert (await _outbox_row(fact_id)).status == "delivered"
    async with async_session_factory() as session:
        repo = SqlAlchemyPaymentRepository(session)
        entry = await repo.find_ledger_entry(
            driver_id=driver_id, entry_type="rewards_bonus", reference_type="rewards_action", reference_id=action_id
        )
        wallet = await repo.get_or_create_wallet(driver_id)
    assert entry is not None and entry.amount == Decimal("1000")
    assert entry.description == "Bonus DIDDI : Bonus d'accueil"
    assert wallet.balance == Decimal("1000")
    ours = [call for call in rewards.done if call["action_id"] == action_id]
    assert len(ours) == 2
    assert {call["status"] for call in ours} == {"done"}
    assert {call["reference"] for call in ours} == {str(entry.id)}
    await engine.dispose()


@pytest.mark.asyncio
async def test_unknown_driver_is_reported_failed_without_credit() -> None:
    action_id = uuid4()
    rewards = FakeRewards()
    status = await rewards_events.do_action(rewards, {
        "type": "credit_professional", "action_id": str(action_id), "professional_id": str(uuid4()),
        "amount_minor": 500, "currency": "XOF", "offer_id": str(uuid4()), "offer_name": "x",
    })
    assert status == "failed"
    assert rewards.done[0]["reason"] == "unknown_driver" and rewards.done[0]["reference"] is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_rewards_down_keeps_the_fact_for_later() -> None:
    fact_id = await _queue_fact(uuid4())
    await rewards_events.run_rewards_facts_once(
        FakeRewards(error=ApiError(503, "REWARDS_UNAVAILABLE", "down")), limit=500
    )
    row = await _outbox_row(fact_id)
    assert row.status == "retry" and row.attempts == 1 and row.next_attempt_at > datetime.now(UTC)
    await engine.dispose()


@pytest.mark.asyncio
async def test_missing_scope_is_retried_not_dropped() -> None:
    fact_id = await _queue_fact(uuid4())
    await rewards_events.run_rewards_facts_once(
        FakeRewards(error=ApiError(403, "REWARDS_OPERATION_FAILED", "scope")), limit=500
    )
    assert (await _outbox_row(fact_id)).status == "retry"
    await engine.dispose()


@pytest.mark.asyncio
async def test_refused_fact_is_kept_as_failed_and_not_resent() -> None:
    fact_id = await _queue_fact(uuid4())
    await rewards_events.run_rewards_facts_once(
        FakeRewards(error=ApiError(422, "REWARDS_OPERATION_FAILED", "bad")), limit=500
    )
    assert (await _outbox_row(fact_id)).status == "failed"
    second = FakeRewards()
    await rewards_events.run_rewards_facts_once(second, limit=500)
    assert fact_id not in {fact["fact_id"] for fact in second.facts}
    await engine.dispose()


@pytest.mark.asyncio
async def test_old_stream_events_are_never_sent_as_facts() -> None:
    ride_id = uuid4()
    async with async_session_factory() as session:
        await SqlAlchemyPaymentRepository(session).enqueue_rewards_event(
            event_type="ride.payment_confirmed", ride_id=ride_id,
            payload={"event_id": f"diddigo:ride.payment_confirmed:{ride_id}:x"},
        )
        await session.commit()
    rewards = FakeRewards()
    await rewards_events.run_rewards_facts_once(rewards, limit=500)
    assert all(fact.get("type") in rewards_events.FACT_TYPES for fact in rewards.facts)
    await engine.dispose()


@pytest.mark.asyncio
async def test_nothing_is_sent_while_rewards_is_switched_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rewards_events.settings, "diddi_rewards_enabled", False)
    rewards = FakeRewards()
    assert await rewards_events.run_rewards_facts_once(rewards) == 0
    assert rewards.facts == []
