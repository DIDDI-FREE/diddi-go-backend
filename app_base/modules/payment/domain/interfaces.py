"""Payment domain interfaces — repository protocol.

The payment module has no external adapter yet (DiddiPay comes later).
The sole protocol defined here — `PaymentRepository` — covers the
PostgreSQL backing that today's cash-only implementation uses."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app_base.modules.payment.domain.entities import Transaction


class PaymentRepository(Protocol):
    async def save(self, transaction: Transaction) -> Transaction: ...

    async def find_by_ride_id(self, ride_id: UUID) -> Transaction | None: ...

    async def update_collected(
        self,
        transaction_id: UUID,
        collected_by: UUID,
        amount: object,
        collected_at: object,
    ) -> Transaction:
        """Mark the cash transaction as collected. `amount` can be Decimal;
        `collected_at` is a datetime. Protocols use `object` to keep the
        type definition loose — concrete signatures in the implementation."""
        ...
