"""Payment domain interfaces."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app_base.modules.payment.domain.entities import (
    KEEP,
    DriverLedgerEntry,
    DriverTopup,
    DriverWallet,
    Transaction,
)


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
        next_action: Any = KEEP,
    ) -> Transaction: ...

    async def list_stale_transactions(
        self,
        *,
        created_before: datetime,
        created_after: datetime,
        limit: int,
    ) -> list[Transaction]:
        """Provider-backed transactions still awaiting a final DiddiPay callback."""
        ...

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

    async def get_or_create_wallet(self, driver_id: UUID, *, currency: str = "XOF") -> DriverWallet: ...

    async def list_ledger_entries(
        self,
        driver_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DriverLedgerEntry], int]: ...

    async def record_ledger_entry_once(self, entry: DriverLedgerEntry) -> DriverLedgerEntry | None:
        """Return None when the same entry was already recorded."""
        ...

    async def save_topup(self, topup: DriverTopup) -> DriverTopup: ...

    async def find_topup_by_id(self, topup_id: UUID) -> DriverTopup | None: ...

    async def find_topup_by_payment_intent_id(self, payment_intent_id: UUID) -> DriverTopup | None: ...

    async def mark_topup_status(
        self,
        topup_id: UUID,
        status: object,
        provider_status: str | None,
        paid_at: object | None,
        next_action: Any = KEEP,
    ) -> DriverTopup: ...

    async def list_stale_topups(
        self,
        *,
        created_before: datetime,
        created_after: datetime,
        limit: int,
    ) -> list[DriverTopup]:
        """Topups still awaiting a final DiddiPay callback."""
        ...
