"""Facts protocol with DiddiRewards (Rewards contract 069, tickets 049 and 066).

DiddiGo reports what happened to a ride (`order.paid`, `order.refunded`, `order.cancelled`).
Rewards decides what it is worth and may answer with actions. Today one action exists,
`credit_professional`: pay a driver a bonus. DiddiGo writes one wallet line per action
(idempotent on `action_id`), then confirms the action to Rewards.

Facts wait in `payment.rewards_event_outbox` and are sent unchanged until Rewards accepts
them. They replace the old Redis stream `diddigo.events.v1` (ticket 064, superseded).
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from app_base.core.database import async_session_factory
from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.core.telemetry import worker_iteration
from app_base.modules.payment.domain.entities import (
    DriverLedgerEntry,
    WalletEntryDirection,
    WalletEntryStatus,
    WalletEntryType,
)
from app_base.modules.payment.infra.repositories import SqlAlchemyPaymentRepository
from app_base.modules.ride.infra.diddirewards_client import DiddiRewardsClient
from app_base.modules.ride.infra.repositories import SqlAlchemyDriverProfileRepository

logger = logging.getLogger(__name__)

FACT_TYPES = ("order.paid", "order.refunded", "order.cancelled")
# Rewards answers these when the fact itself is wrong: resending the same fact cannot help.
# 401/403 are not here: a missing scope is fixed in configuration, then the fact goes through.
FINAL_REFUSAL_STATUS_CODES = frozenset({400, 404, 409, 422})
ACTIONS_POLL_SECONDS = 60
ACTION_REFERENCE_TYPE = "rewards_action"


def _ready(diddirewards: DiddiRewardsClient | None) -> bool:
    return settings.diddi_rewards_enabled and diddirewards is not None and diddirewards.configured


async def run_rewards_facts_once(diddirewards: DiddiRewardsClient | None, *, limit: int | None = None) -> int:
    """Send due facts; do the actions in the answers. Returns the number of facts accepted."""
    if not _ready(diddirewards):
        return 0
    actions: list[dict] = []
    delivered = 0
    async with async_session_factory() as session:
        repository = SqlAlchemyPaymentRepository(session)
        events = await repository.list_due_rewards_events(
            now=datetime.now(UTC),
            limit=limit or settings.diddi_rewards_events_batch_size,
            event_types=FACT_TYPES,
        )
        for event in events:
            try:
                answer = await diddirewards.report_fact(fact=event.payload, request_id=event.event_id)
            except ApiError as exc:
                if exc.status_code in FINAL_REFUSAL_STATUS_CODES:
                    await repository.mark_rewards_event_failed(
                        event, now=datetime.now(UTC), error=f"{exc.status_code} {exc.details}"
                    )
                    log_event(
                        "rewards.fact.refused", level="error", fact_id=event.event_id,
                        status_code=exc.status_code,
                    )
                    continue
                await _retry_later(repository, event, error=f"{exc.status_code} {exc.code}")
                continue
            except Exception as exc:  # noqa: BLE001 - a fact is never dropped
                await _retry_later(repository, event, error=repr(exc))
                continue
            await repository.mark_rewards_event_delivered(event, now=datetime.now(UTC))
            delivered += 1
            log_event(
                "rewards.fact.reported", fact_id=event.event_id, status=answer.get("status"),
                actions=len(answer.get("actions") or []),
            )
            actions.extend(answer.get("actions") or [])
        await session.commit()
    for action in actions:
        await do_action(diddirewards, action)
    return delivered


async def _retry_later(repository: SqlAlchemyPaymentRepository, event, *, error: str) -> None:
    delay = min(
        settings.diddi_rewards_events_retry_base_seconds * 2 ** min(event.attempts, 8),
        settings.diddi_rewards_events_retry_max_seconds,
    )
    now = datetime.now(UTC)
    await repository.mark_rewards_event_retry(
        event, now=now, next_attempt_at=now + timedelta(seconds=delay), error=error
    )
    log_event("rewards.fact.retry", level="warning", fact_id=event.event_id, attempts=event.attempts)


async def run_rewards_actions_once(diddirewards: DiddiRewardsClient | None) -> int:
    """Do every action Rewards still waits for (a credit or a confirm that failed earlier)."""
    if not _ready(diddirewards):
        return 0
    answer = await diddirewards.pending_actions(request_id=f"diddigo-actions-{int(time.time())}")
    actions = answer.get("actions") or []
    for action in actions:
        await do_action(diddirewards, action)
    return len(actions)


async def do_action(diddirewards: DiddiRewardsClient, action: dict) -> str:
    """Do one Rewards action and confirm it. Returns `done`, `failed` or `skipped`."""
    if action.get("type", "credit_professional") != "credit_professional":
        log_event("rewards.action.unknown_type", level="error", action=str(action)[:300])
        return "skipped"
    try:
        action_id = UUID(str(action["action_id"]))
    except (KeyError, ValueError):
        log_event("rewards.action.invalid", level="error", action=str(action)[:300])
        return "skipped"
    try:
        reference, failure = await _credit_professional(action_id, action)
    except Exception:  # noqa: BLE001 - nothing was confirmed; Rewards lists the action again
        logger.exception("rewards action credit failed action_id=%s", action_id)
        return "skipped"
    status = "failed" if failure else "done"
    try:
        await diddirewards.action_done(
            action_id=action_id,
            status=status,
            reference=reference,
            reason=failure,
            idempotency_key=f"diddigo:action:{action_id}:{status}:{int(time.time())}",
            request_id=f"diddigo-action-{action_id}",
        )
    except Exception:  # noqa: BLE001 - the credit stays; the confirm is retried from the pending list
        logger.exception("rewards action confirm failed action_id=%s", action_id)
        log_event("rewards.action.confirm_deferred", level="warning", action_id=action_id)
        return "skipped"
    log_event("rewards.action.confirmed", action_id=action_id, status=status, reason=failure)
    return status


async def _credit_professional(action_id: UUID, action: dict) -> tuple[str | None, str | None]:
    """Write the bonus line once. Returns (wallet entry id, None) or (None, failure reason)."""
    try:
        amount = Decimal(str(action.get("amount_minor")))
        professional_id = UUID(str(action.get("professional_id")))
    except (InvalidOperation, ValueError):
        return None, "invalid_action"
    currency = str(action.get("currency") or "XOF")
    if amount <= 0:
        return None, "invalid_amount"
    if currency != "XOF":
        return None, "unsupported_currency"
    async with async_session_factory() as session:
        drivers = SqlAlchemyDriverProfileRepository(session)
        payments = SqlAlchemyPaymentRepository(session)
        profile = await drivers.find_by_user_id(professional_id)
        if profile is None:
            return None, "unknown_driver"
        offer_name = str(action.get("offer_name") or "").strip()
        entry = DriverLedgerEntry(
            id=DriverLedgerEntry.new_id(),
            driver_id=profile.id,
            amount=amount,
            currency=currency,
            direction=WalletEntryDirection.CREDIT,
            entry_type=WalletEntryType.REWARDS_BONUS,
            status=WalletEntryStatus.CONFIRMED,
            reference_type=ACTION_REFERENCE_TYPE,
            reference_id=action_id,
            description=(f"Bonus DIDDI : {offer_name}" if offer_name else "Bonus DIDDI")[:500],
            created_at=datetime.now(UTC),
        )
        credited = await payments.record_ledger_entry_once(entry)
        if credited is None:
            # Already paid by an earlier attempt: confirm with that line.
            existing = await payments.find_ledger_entry(
                driver_id=profile.id,
                entry_type=WalletEntryType.REWARDS_BONUS.value,
                reference_type=ACTION_REFERENCE_TYPE,
                reference_id=action_id,
            )
            await session.commit()
            return (str(existing.id) if existing else None), None
        await session.commit()
        log_event(
            "payment.rewards_bonus.credited", action_id=action_id, driver_id=profile.id,
            amount=amount, offer_id=action.get("offer_id"),
        )
        return str(credited.id), None


async def rewards_events_loop(diddirewards: DiddiRewardsClient | None) -> None:
    last_actions_poll = 0.0
    while True:
        try:
            await asyncio.sleep(settings.diddi_rewards_events_delivery_interval_seconds)
            with worker_iteration("rewards-events"):
                await run_rewards_facts_once(diddirewards)
                if time.monotonic() - last_actions_poll >= ACTIONS_POLL_SECONDS:
                    last_actions_poll = time.monotonic()
                    await run_rewards_actions_once(diddirewards)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("rewards facts sweep failed")
