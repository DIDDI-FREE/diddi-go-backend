"""SQLAlchemy-backed payment repository — replaces the stub that always
returned None from `get_by_ride_id`.

Maps between `payment.domain.entities.Transaction` and the ORM
`TransactionModel` in `payment.infra.models`.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.payment.domain.entities import (
    PaymentMethod,
    PaymentStatus,
    Transaction,
)
from app_base.modules.payment.infra import models as orm


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, transaction: Transaction) -> Transaction:
        row = orm.TransactionModel(
            id=transaction.id,
            ride_id=transaction.ride_id,
            amount=transaction.amount,
            currency=transaction.currency,
            method=transaction.method.value,
            status=transaction.status.value,
            collected_by=transaction.collected_by,
            collected_at=transaction.collected_at,
            created_at=transaction.created_at or datetime.utcnow(),
        )
        self._session.add(row)
        await self._session.flush()
        return transaction

    async def find_by_ride_id(self, ride_id: UUID) -> Transaction | None:
        result = await self._session.execute(
            select(orm.TransactionModel).where(orm.TransactionModel.ride_id == ride_id),
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def update_collected(
        self,
        transaction_id: UUID,
        collected_by: UUID,
        amount: Any,
        collected_at: Any,
    ) -> Transaction:
        row = await self._session.get(orm.TransactionModel, transaction_id)
        if row is None:
            raise LookupError(f"No transaction with id={transaction_id}")
        row.collected_by = collected_by
        row.amount = amount
        row.collected_at = collected_at
        row.status = PaymentStatus.COLLECTED.value
        await self._session.flush()
        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: orm.TransactionModel) -> Transaction:
        return Transaction(
            id=row.id,
            ride_id=row.ride_id,
            amount=Decimal(str(row.amount)),
            currency=row.currency,
            method=PaymentMethod(row.method),
            status=PaymentStatus(row.status),
            collected_by=row.collected_by,
            collected_at=row.collected_at,
            created_at=row.created_at,
        )
