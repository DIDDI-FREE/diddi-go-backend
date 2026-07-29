from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PaymentTransaction:
    ride_id: str
    amount: float
    currency: str
    status: str


class PaymentProvider(Protocol):
    """Cash-only at launch; batch 7+ wires a real PaymentRepository behind
    this protocol. A later iteration (DiddiPay) replaces it without touching
    any service-layer caller.

    Implementations are async — the database is accessed via an async session
    so `create_transaction` / `confirm` can round-trip in the same event loop
    as the HTTP request.
    """

    async def create_transaction(self, ride_id: str, amount: float, currency: str) -> PaymentTransaction: ...

    async def confirm(self, ride_id: str, collector_id: str) -> PaymentTransaction: ...
