"""SQLAlchemy-backed payment repository — replaces the stub that always
returned None from `get_by_ride_id`.

Maps between `payment.domain.entities.Transaction` and the ORM
`TransactionModel` in `payment.infra.models`.
"""

from __future__ import annotations

from datetime import UTC, datetime
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
    DriverWithdrawal,
    DriverWithdrawalQuote,
    PaymentMethod,
    PaymentStatus,
    TopupStatus,
    Transaction,
    WalletEntryDirection,
    WalletEntryStatus,
    WalletEntryType,
    WithdrawalStatus,
)
from app_base.modules.payment.infra import models as orm


class SqlAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

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

    async def withdrawal_reserved_total(self, driver_id: UUID) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(orm.DriverWithdrawalModel.amount), 0)).where(
                orm.DriverWithdrawalModel.driver_id == driver_id,
                orm.DriverWithdrawalModel.status.in_(("reserved", "processing")),
            )
        )
        return Decimal(str(result.scalar_one()))

    async def list_ledger_entries(
        self,
        driver_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DriverLedgerEntry], int]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(orm.DriverLedgerEntryModel)
            .where(
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

    async def save_withdrawal_quote(self, quote: DriverWithdrawalQuote) -> DriverWithdrawalQuote:
        self._session.add(
            orm.DriverWithdrawalQuoteModel(
                id=quote.id,
                driver_id=quote.driver_id,
                amount=quote.amount,
                fees=quote.fees,
                net_amount=quote.net_amount,
                currency=quote.currency,
                expires_at=quote.expires_at,
                created_at=quote.created_at or datetime.now(UTC),
            )
        )
        await self._session.flush()
        return quote

    async def reserve_withdrawal_from_quote(self, withdrawal: DriverWithdrawal, *, now: datetime) -> DriverWithdrawal:
        quote_result = await self._session.execute(
            select(orm.DriverWithdrawalQuoteModel)
            .where(orm.DriverWithdrawalQuoteModel.id == withdrawal.quote_id)
            .with_for_update()
        )
        quote = quote_result.scalar_one_or_none()
        if quote is None or quote.driver_id != withdrawal.driver_id:
            raise LookupError("WITHDRAWAL_QUOTE_NOT_FOUND")
        if quote.consumed_at is not None:
            existing = await self._session.execute(
                select(orm.DriverWithdrawalModel).where(orm.DriverWithdrawalModel.quote_id == withdrawal.quote_id)
            )
            row = existing.scalar_one_or_none()
            if row is not None:
                return self._withdrawal_to_domain(row)
            raise LookupError("WITHDRAWAL_QUOTE_ALREADY_USED")
        expires_at = quote.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= now:
            raise LookupError("WITHDRAWAL_QUOTE_EXPIRED")

        withdrawal.amount = Decimal(str(quote.amount))
        withdrawal.fees = Decimal(str(quote.fees))
        withdrawal.net_amount = Decimal(str(quote.net_amount))
        withdrawal.currency = quote.currency

        wallet_result = await self._session.execute(
            select(orm.DriverWalletModel)
            .where(orm.DriverWalletModel.driver_id == withdrawal.driver_id)
            .with_for_update()
        )
        wallet = wallet_result.scalar_one_or_none()
        if wallet is None:
            await self.get_or_create_wallet(withdrawal.driver_id, currency=withdrawal.currency)
            wallet_result = await self._session.execute(
                select(orm.DriverWalletModel)
                .where(orm.DriverWalletModel.driver_id == withdrawal.driver_id)
                .with_for_update()
            )
            wallet = wallet_result.scalar_one()
        if Decimal(str(wallet.balance)) < withdrawal.amount:
            raise LookupError("WITHDRAWAL_BALANCE_INSUFFICIENT")

        row = orm.DriverWithdrawalModel(
            id=withdrawal.id,
            driver_id=withdrawal.driver_id,
            quote_id=withdrawal.quote_id,
            amount=withdrawal.amount,
            fees=withdrawal.fees,
            net_amount=withdrawal.net_amount,
            currency=withdrawal.currency,
            beneficiary_reference=withdrawal.beneficiary_reference,
            status=WithdrawalStatus.RESERVED.value,
            business_reference=withdrawal.business_reference,
            idempotency_key=withdrawal.idempotency_key,
            created_at=now,
            reserved_at=now,
            updated_at=now,
        )
        self._session.add(row)
        quote.consumed_at = now
        wallet.balance = Decimal(str(wallet.balance)) - withdrawal.amount
        wallet.updated_at = now
        self._session.add(
            orm.DriverLedgerEntryModel(
                id=DriverLedgerEntry.new_id(),
                driver_id=withdrawal.driver_id,
                amount=withdrawal.amount,
                currency=withdrawal.currency,
                direction=WalletEntryDirection.DEBIT.value,
                entry_type=WalletEntryType.WITHDRAWAL_RESERVED.value,
                status=WalletEntryStatus.CONFIRMED.value,
                reference_type="driver_withdrawal",
                reference_id=withdrawal.id,
                description="Montant reserve pour retrait chauffeur",
                created_at=now,
            )
        )
        await self._session.flush()
        return self._withdrawal_to_domain(row)

    async def find_withdrawal_by_id(self, withdrawal_id: UUID) -> DriverWithdrawal | None:
        row = await self._session.get(orm.DriverWithdrawalModel, withdrawal_id)
        return self._withdrawal_to_domain(row) if row else None

    async def find_withdrawal_by_payout_id(self, payout_id: UUID) -> DriverWithdrawal | None:
        result = await self._session.execute(
            select(orm.DriverWithdrawalModel).where(orm.DriverWithdrawalModel.payout_id == payout_id)
        )
        row = result.scalar_one_or_none()
        return self._withdrawal_to_domain(row) if row else None

    async def find_withdrawal_by_business_reference(self, business_reference: str) -> DriverWithdrawal | None:
        result = await self._session.execute(
            select(orm.DriverWithdrawalModel).where(orm.DriverWithdrawalModel.business_reference == business_reference)
        )
        row = result.scalar_one_or_none()
        return self._withdrawal_to_domain(row) if row else None

    async def list_withdrawals(
        self, driver_id: UUID, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[DriverWithdrawal], int]:
        total = int(
            (
                await self._session.execute(
                    select(func.count())
                    .select_from(orm.DriverWithdrawalModel)
                    .where(orm.DriverWithdrawalModel.driver_id == driver_id)
                )
            ).scalar_one()
        )
        rows = await self._session.execute(
            select(orm.DriverWithdrawalModel)
            .where(orm.DriverWithdrawalModel.driver_id == driver_id)
            .order_by(orm.DriverWithdrawalModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [self._withdrawal_to_domain(row) for row in rows.scalars().all()], total

    async def list_stale_withdrawals(self, *, updated_before: datetime, limit: int) -> list[DriverWithdrawal]:
        rows = await self._session.execute(
            select(orm.DriverWithdrawalModel)
            .where(
                orm.DriverWithdrawalModel.status.in_(("reserved", "processing")),
                orm.DriverWithdrawalModel.updated_at <= updated_before,
            )
            .order_by(orm.DriverWithdrawalModel.updated_at.asc())
            .limit(limit)
        )
        return [self._withdrawal_to_domain(row) for row in rows.scalars().all()]

    async def mark_withdrawal_provider_state(
        self,
        withdrawal_id: UUID,
        *,
        status: object,
        payout_id: UUID | None,
        provider_status: str | None,
        failure_code: str | None = None,
        failure_message: str | None = None,
        now: datetime,
    ) -> DriverWithdrawal:
        result = await self._session.execute(
            select(orm.DriverWithdrawalModel).where(orm.DriverWithdrawalModel.id == withdrawal_id).with_for_update()
        )
        row = result.scalar_one()
        target = status if isinstance(status, WithdrawalStatus) else WithdrawalStatus(str(status))
        if row.status in (WithdrawalStatus.SUCCEEDED.value, WithdrawalStatus.RELEASED.value):
            return self._withdrawal_to_domain(row)
        row.payout_id = payout_id or row.payout_id
        row.provider_status = provider_status
        row.failure_code = failure_code
        row.failure_message = failure_message
        row.updated_at = now
        if target is WithdrawalStatus.SUCCEEDED:
            row.status = target.value
            row.succeeded_at = now
            await self._insert_withdrawal_ledger_once(
                row, WalletEntryType.WITHDRAWAL_SUCCEEDED, WalletEntryDirection.DEBIT, now
            )
        elif target in (WithdrawalStatus.FAILED, WithdrawalStatus.RELEASED):
            row.status = WithdrawalStatus.RELEASED.value
            row.released_at = now
            inserted = await self._insert_withdrawal_ledger_once(
                row, WalletEntryType.WITHDRAWAL_RELEASED, WalletEntryDirection.CREDIT, now
            )
            if inserted:
                wallet_result = await self._session.execute(
                    select(orm.DriverWalletModel)
                    .where(orm.DriverWalletModel.driver_id == row.driver_id)
                    .with_for_update()
                )
                wallet = wallet_result.scalar_one()
                wallet.balance = Decimal(str(wallet.balance)) + Decimal(str(row.amount))
                wallet.updated_at = now
        else:
            row.status = target.value
        await self._session.flush()
        return self._withdrawal_to_domain(row)

    async def _insert_withdrawal_ledger_once(
        self,
        row: orm.DriverWithdrawalModel,
        entry_type: WalletEntryType,
        direction: WalletEntryDirection,
        now: datetime,
    ) -> bool:
        stmt = (
            insert(orm.DriverLedgerEntryModel)
            .values(
                id=DriverLedgerEntry.new_id(),
                driver_id=row.driver_id,
                amount=row.amount,
                currency=row.currency,
                direction=direction.value,
                entry_type=entry_type.value,
                status=WalletEntryStatus.CONFIRMED.value,
                reference_type="driver_withdrawal",
                reference_id=row.id,
                description=entry_type.value,
                created_at=now,
            )
            .on_conflict_do_nothing(
                index_elements=[
                    orm.DriverLedgerEntryModel.driver_id,
                    orm.DriverLedgerEntryModel.entry_type,
                    orm.DriverLedgerEntryModel.reference_type,
                    orm.DriverLedgerEntryModel.reference_id,
                ]
            )
        )
        result = await self._session.execute(stmt)
        return bool(result.rowcount)

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

    @staticmethod
    def _withdrawal_to_domain(row: orm.DriverWithdrawalModel) -> DriverWithdrawal:
        return DriverWithdrawal(
            id=row.id,
            driver_id=row.driver_id,
            quote_id=row.quote_id,
            amount=Decimal(str(row.amount)),
            fees=Decimal(str(row.fees)),
            net_amount=Decimal(str(row.net_amount)),
            currency=row.currency,
            beneficiary_reference=row.beneficiary_reference,
            status=WithdrawalStatus(row.status),
            payout_id=row.payout_id,
            business_reference=row.business_reference,
            idempotency_key=row.idempotency_key,
            provider_status=row.provider_status,
            failure_code=row.failure_code,
            failure_message=row.failure_message,
            created_at=row.created_at,
            reserved_at=row.reserved_at,
            succeeded_at=row.succeeded_at,
            released_at=row.released_at,
            updated_at=row.updated_at,
        )
