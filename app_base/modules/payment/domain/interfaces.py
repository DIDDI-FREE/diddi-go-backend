"""Payment domain interfaces."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app_base.modules.payment.domain.entities import Transaction


class PaymentRepository(Protocol):
    async def save(self, transaction: Transaction) -> Transaction: ...

    async def find_by_ride_id(self, ride_id: UUID) -> Transaction | None: ...

    async def find_by_payment_intent_id(self, payment_intent_id: UUID) -> Transaction | None: ...

    async def update_collected(
        self,
        transaction_id: UUID,
        collected_by: UUID,
        amount: object,
        collected_at: object,
    ) -> Transaction: ...

    async def mark_external_status(
        self,
        transaction_id: UUID,
        status: object,
        provider_status: str | None,
        paid_at: object | None,
    ) -> Transaction: ...

    async def record_webhook_event(
        self,
        *,
        event_id: str,
        payment_intent_id: UUID | None,
        event_type: str,
        business_reference: str | None,
        payload: str,
    ) -> bool:
        """Return False when the event has already been processed."""
        ...
