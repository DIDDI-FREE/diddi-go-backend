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

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.payment.domain.entities import (
    KEEP,
    PENDING_PAYMENT_STATUSES,
    PENDING_TOPUP_STATUSES,
    DriverLedgerEntry,
    DriverTopup,
    DriverWallet,
    PaymentMethod,
    PaymentStatus,
    TopupStatus,
    Transaction,
    WalletEntryDirection,
    WalletEntryStatus,
    WalletEntryType,
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
            payment_intent_id=transaction.payment_intent_id,
            business_reference=transaction.business_reference,
            idempotency_key=transaction.idempotency_key,
            provider_status=transaction.provider_status,
            provider_next_action=transaction.provider_next_action,
            paid_at=transaction.paid_at,
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

    async def find_by_payment_intent_id(self, payment_intent_id: UUID) -> Transaction | None:
        result = await self._session.execute(
            select(orm.TransactionModel).where(orm.TransactionModel.payment_intent_id == payment_intent_id),
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

    async def mark_external_status(
        self,
        transaction_id: UUID,
        status: Any,
        provider_status: str | None,
        paid_at: Any | None,
        next_action: Any = KEEP,
    ) -> Transaction:
        row = await self._session.get(orm.TransactionModel, transaction_id)
        if row is None:
            raise LookupError(f"No transaction with id={transaction_id}")
        row.status = status.value if isinstance(status, PaymentStatus) else str(status)
        row.provider_status = provider_status
        if paid_at is not None:
            row.paid_at = paid_at
            row.collected_at = paid_at
        if next_action is not KEEP:
            row.provider_next_action = next_action
        await self._session.flush()
        return self._to_domain(row)

    async def list_stale_transactions(
        self,
        *,
        created_before: datetime,
        created_after: datetime,
        limit: int,
    ) -> list[Transaction]:
        result = await self._session.execute(
            select(orm.TransactionModel)
            .where(
                orm.TransactionModel.payment_intent_id.is_not(None),
                orm.TransactionModel.status.in_([s.value for s in PENDING_PAYMENT_STATUSES]),
                orm.TransactionModel.created_at <= created_before,
                orm.TransactionModel.created_at >= created_after,
            )
            .order_by(orm.TransactionModel.created_at.asc())
            .limit(limit),
        )
        return [self._to_domain(row) for row in result.scalars().all()]

    async def record_webhook_event(
        self,
        *,
        event_id: str,
        payment_intent_id: UUID | None,
        event_type: str,
        business_reference: str | None,
        payload: str,
    ) -> bool:
        stmt = (
            insert(orm.PaymentWebhookEventModel)
            .values(
                id=event_id,
                payment_intent_id=payment_intent_id,
                event_type=event_type,
                business_reference=business_reference,
                payload=payload,
            )
            .on_conflict_do_nothing(index_elements=[orm.PaymentWebhookEventModel.id])
        )
        result = await self._session.execute(stmt)
        return bool(result.rowcount)

    async def get_or_create_wallet(self, driver_id: UUID, *, currency: str = "XOF") -> DriverWallet:
        result = await self._session.execute(
            select(orm.DriverWalletModel).where(orm.DriverWalletModel.driver_id == driver_id),
        )
        row = result.scalar_one_or_none()
        if row is None:
            stmt = (
                insert(orm.DriverWalletModel)
                .values(
                    id=DriverWallet.new_id(),
                    driver_id=driver_id,
                    balance=Decimal("0"),
                    currency=currency,
                )
                .on_conflict_do_nothing(index_elements=[orm.DriverWalletModel.driver_id])
            )
            await self._session.execute(stmt)
            result = await self._session.execute(
                select(orm.DriverWalletModel).where(orm.DriverWalletModel.driver_id == driver_id),
            )
            row = result.scalar_one()
        return self._wallet_to_domain(row)

    async def list_ledger_entries(
        self,
        driver_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DriverLedgerEntry], int]:
        count_result = await self._session.execute(
            select(func.count()).select_from(orm.DriverLedgerEntryModel).where(
                orm.DriverLedgerEntryModel.driver_id == driver_id,
            ),
        )
        total = int(count_result.scalar_one())
        result = await self._session.execute(
            select(orm.DriverLedgerEntryModel)
            .where(orm.DriverLedgerEntryModel.driver_id == driver_id)
            .order_by(orm.DriverLedgerEntryModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size),
        )
        return [self._ledger_to_domain(row) for row in result.scalars().all()], total

    async def record_ledger_entry_once(self, entry: DriverLedgerEntry) -> DriverLedgerEntry | None:
        await self.get_or_create_wallet(entry.driver_id, currency=entry.currency)
        stmt = (
            insert(orm.DriverLedgerEntryModel)
            .values(
                id=entry.id,
                driver_id=entry.driver_id,
                amount=entry.amount,
                currency=entry.currency,
                direction=entry.direction.value,
                entry_type=entry.entry_type.value,
                status=entry.status.value,
                reference_type=entry.reference_type,
                reference_id=entry.reference_id,
                description=entry.description,
                created_at=entry.created_at or datetime.utcnow(),
            )
            .on_conflict_do_nothing(
                index_elements=[
                    orm.DriverLedgerEntryModel.driver_id,
                    orm.DriverLedgerEntryModel.entry_type,
                    orm.DriverLedgerEntryModel.reference_type,
                    orm.DriverLedgerEntryModel.reference_id,
                ],
            )
        )
        result = await self._session.execute(stmt)
        if not result.rowcount:
            return None

        wallet_result = await self._session.execute(
            select(orm.DriverWalletModel).where(orm.DriverWalletModel.driver_id == entry.driver_id),
        )
        wallet = wallet_result.scalar_one()
        if entry.status is WalletEntryStatus.CONFIRMED:
            delta = entry.amount if entry.direction is WalletEntryDirection.CREDIT else -entry.amount
            wallet.balance = Decimal(str(wallet.balance)) + Decimal(str(delta))
            wallet.updated_at = datetime.utcnow()
        await self._session.flush()
        return entry

    async def save_topup(self, topup: DriverTopup) -> DriverTopup:
        row = orm.DriverTopupModel(
            id=topup.id,
            driver_id=topup.driver_id,
            amount=topup.amount,
            currency=topup.currency,
            method=topup.method.value,
            status=topup.status.value,
            payment_intent_id=topup.payment_intent_id,
            business_reference=topup.business_reference,
            idempotency_key=topup.idempotency_key,
            provider_status=topup.provider_status,
            provider_next_action=topup.provider_next_action,
            created_at=topup.created_at or datetime.utcnow(),
            paid_at=topup.paid_at,
        )
        self._session.add(row)
        await self._session.flush()
        return topup

    async def find_topup_by_id(self, topup_id: UUID) -> DriverTopup | None:
        row = await self._session.get(orm.DriverTopupModel, topup_id)
        return self._topup_to_domain(row) if row else None

    async def find_topup_by_payment_intent_id(self, payment_intent_id: UUID) -> DriverTopup | None:
        result = await self._session.execute(
            select(orm.DriverTopupModel).where(orm.DriverTopupModel.payment_intent_id == payment_intent_id),
        )
        row = result.scalar_one_or_none()
        return self._topup_to_domain(row) if row else None

    async def mark_topup_status(
        self,
        topup_id: UUID,
        status: Any,
        provider_status: str | None,
        paid_at: Any | None,
        next_action: Any = KEEP,
    ) -> DriverTopup:
        row = await self._session.get(orm.DriverTopupModel, topup_id)
        if row is None:
            raise LookupError(f"No topup with id={topup_id}")
        row.status = status.value if isinstance(status, TopupStatus) else str(status)
        row.provider_status = provider_status
        if paid_at is not None:
            row.paid_at = paid_at
        if next_action is not KEEP:
            row.provider_next_action = next_action
        await self._session.flush()
        return self._topup_to_domain(row)

    async def list_stale_topups(
        self,
        *,
        created_before: datetime,
        created_after: datetime,
        limit: int,
    ) -> list[DriverTopup]:
        result = await self._session.execute(
            select(orm.DriverTopupModel)
            .where(
                orm.DriverTopupModel.payment_intent_id.is_not(None),
                orm.DriverTopupModel.status.in_([s.value for s in PENDING_TOPUP_STATUSES]),
                orm.DriverTopupModel.created_at <= created_before,
                orm.DriverTopupModel.created_at >= created_after,
            )
            .order_by(orm.DriverTopupModel.created_at.asc())
            .limit(limit),
        )
        return [self._topup_to_domain(row) for row in result.scalars().all()]

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
            payment_intent_id=row.payment_intent_id,
            business_reference=row.business_reference,
            idempotency_key=row.idempotency_key,
            provider_status=row.provider_status,
            provider_next_action=row.provider_next_action,
            paid_at=row.paid_at,
        )

    @staticmethod
    def _wallet_to_domain(row: orm.DriverWalletModel) -> DriverWallet:
        return DriverWallet(
            id=row.id,
            driver_id=row.driver_id,
            balance=Decimal(str(row.balance)),
            currency=row.currency,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _ledger_to_domain(row: orm.DriverLedgerEntryModel) -> DriverLedgerEntry:
        return DriverLedgerEntry(
            id=row.id,
            driver_id=row.driver_id,
            amount=Decimal(str(row.amount)),
            currency=row.currency,
            direction=WalletEntryDirection(row.direction),
            entry_type=WalletEntryType(row.entry_type),
            status=WalletEntryStatus(row.status),
            reference_type=row.reference_type,
            reference_id=row.reference_id,
            description=row.description,
            created_at=row.created_at,
        )

    @staticmethod
    def _topup_to_domain(row: orm.DriverTopupModel) -> DriverTopup:
        return DriverTopup(
            id=row.id,
            driver_id=row.driver_id,
            amount=Decimal(str(row.amount)),
            currency=row.currency,
            method=PaymentMethod(row.method),
            status=TopupStatus(row.status),
            payment_intent_id=row.payment_intent_id,
            business_reference=row.business_reference,
            idempotency_key=row.idempotency_key,
            provider_status=row.provider_status,
            provider_next_action=row.provider_next_action,
            created_at=row.created_at,
            paid_at=row.paid_at,
        )
