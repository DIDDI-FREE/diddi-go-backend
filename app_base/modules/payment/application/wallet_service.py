"""Driver wallet use cases for DiddiGo commercial V1."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.settings import settings
from app_base.modules.payment.domain.entities import (
    DriverLedgerEntry,
    DriverTopup,
    PaymentMethod,
    PaymentStatus,
    TopupStatus,
    WalletEntryDirection,
    WalletEntryStatus,
    WalletEntryType,
)
from app_base.modules.payment.domain.interfaces import PaymentRepository
from app_base.modules.payment.infra.diddipay_client import DiddiPayClient
from app_base.modules.ride.domain.entities import Ride
from app_base.modules.ride.domain.interfaces import DriverProfileRepository


@dataclass
class DriverWalletService:
    payment_repo: PaymentRepository
    driver_repo: DriverProfileRepository
    diddipay: DiddiPayClient | None = None

    async def get_wallet(self, *, driver_user_id: UUID) -> dict:
        driver_id = await self._driver_id_for_user(driver_user_id)
        wallet = await self.payment_repo.get_or_create_wallet(driver_id)
        return _wallet_payload(wallet, min_balance=Decimal(settings.driver_min_balance))

    async def get_ledger(self, *, driver_user_id: UUID, page: int = 1, page_size: int = 20) -> dict:
        driver_id = await self._driver_id_for_user(driver_user_id)
        await self.payment_repo.get_or_create_wallet(driver_id)
        entries, total = await self.payment_repo.list_ledger_entries(driver_id, page=page, page_size=page_size)
        return {
            "data": [_ledger_payload(entry) for entry in entries],
            "pagination": {"page": page, "page_size": page_size, "total": total},
        }

    async def admin_get_wallet(self, driver_id: UUID) -> dict:
        await self._require_driver(driver_id)
        wallet = await self.payment_repo.get_or_create_wallet(driver_id)
        return _wallet_payload(wallet, min_balance=Decimal(settings.driver_min_balance))

    async def admin_get_ledger(self, driver_id: UUID, *, page: int = 1, page_size: int = 20) -> dict:
        await self._require_driver(driver_id)
        await self.payment_repo.get_or_create_wallet(driver_id)
        entries, total = await self.payment_repo.list_ledger_entries(driver_id, page=page, page_size=page_size)
        return {
            "driver_id": str(driver_id),
            "data": [_ledger_payload(entry) for entry in entries],
            "pagination": {"page": page, "page_size": page_size, "total": total},
        }

    async def ensure_driver_can_go_online(self, driver_id: UUID) -> None:
        min_balance = Decimal(settings.driver_min_balance)
        if min_balance <= 0:
            return
        wallet = await self.payment_repo.get_or_create_wallet(driver_id)
        if wallet.balance < min_balance:
            raise ApiError(
                403,
                "DRIVER_BALANCE_TOO_LOW",
                "Solde chauffeur insuffisant pour passer en ligne.",
                {"balance": int(wallet.balance), "min_balance": int(min_balance), "currency": wallet.currency},
            )

    async def create_topup(
        self,
        *,
        driver_user_id: UUID,
        amount: Decimal,
        method: str,
        customer_email: str,
        customer_phone: str | None = None,
        callback_url: str | None = None,
    ) -> dict:
        driver_id = await self._driver_id_for_user(driver_user_id)
        if amount <= 0:
            raise ApiError(422, "INVALID_TOPUP_AMOUNT", "Le montant de recharge doit etre positif.")
        try:
            payment_method = PaymentMethod(method)
        except ValueError as exc:
            raise ApiError(422, ErrorCode.INVALID_PAYMENT_METHOD, "Methode de paiement invalide.") from exc
        if payment_method is PaymentMethod.CASH:
            raise ApiError(422, ErrorCode.INVALID_PAYMENT_METHOD, "La recharge cash n'est pas supportee.")
        if not customer_email:
            raise ApiError(
                422,
                ErrorCode.PAYMENT_EMAIL_REQUIRED,
                "Un email client est requis pour initialiser une recharge DiddiPay/Paystack.",
                {"field": "customer_email"},
            )

        topup_id = DriverTopup.new_id()
        idempotency_key = f"driver_topup:{topup_id}:v1"
        business_reference = f"driver_topup:{topup_id}"
        intent = await (self.diddipay or DiddiPayClient()).create_payment_intent(
            {
                "business_reference": business_reference,
                "amount": int(amount),
                "currency": "XOF",
                "payer_user_id": str(driver_user_id),
                "payee_user_id": None,
                "channel": "mobile_money",
                "network": "wave" if payment_method is PaymentMethod.WAVE else None,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "callback_url": callback_url or settings.diddigo_payment_callback_url,
                "description": f"Recharge compte chauffeur DiddiGo {driver_id}",
                "metadata": {"driver_id": str(driver_id), "topup_id": str(topup_id)},
            },
            idempotency_key=idempotency_key,
        )
        status = _topup_status_from_payment_status(_payment_status_from_diddipay(str(intent.get("status") or "")))
        next_action = _next_action_from_intent(intent)
        topup = DriverTopup(
            id=topup_id,
            driver_id=driver_id,
            amount=Decimal(str(intent.get("amount") or amount)),
            currency=str(intent.get("currency") or "XOF"),
            method=payment_method,
            status=status,
            payment_intent_id=UUID(str(intent["id"])),
            business_reference=business_reference,
            idempotency_key=idempotency_key,
            provider_status=str(intent.get("status") or status.value),
            provider_next_action=next_action,
            created_at=datetime.now(UTC),
            paid_at=datetime.now(UTC) if status is TopupStatus.SUCCEEDED else None,
        )
        await self.payment_repo.save_topup(topup)
        if status is TopupStatus.SUCCEEDED:
            await self.credit_topup(topup)
        return _topup_payload(topup, next_action=next_action)

    async def get_topup(self, *, driver_user_id: UUID, topup_id: UUID) -> dict:
        driver_id = await self._driver_id_for_user(driver_user_id)
        topup = await self.payment_repo.find_topup_by_id(topup_id)
        if topup is None or topup.driver_id != driver_id:
            raise ApiError(404, ErrorCode.TOPUP_NOT_FOUND, "Recharge chauffeur introuvable.")
        return _topup_payload(topup, next_action=topup.provider_next_action)

    async def credit_topup(self, topup: DriverTopup) -> None:
        if topup.status is not TopupStatus.SUCCEEDED:
            return
        await self.payment_repo.record_ledger_entry_once(
            DriverLedgerEntry(
                id=DriverLedgerEntry.new_id(),
                driver_id=topup.driver_id,
                amount=topup.amount,
                currency=topup.currency,
                direction=WalletEntryDirection.CREDIT,
                entry_type=WalletEntryType.TOPUP,
                status=WalletEntryStatus.CONFIRMED,
                reference_type="driver_topup",
                reference_id=topup.id,
                description="Recharge chauffeur confirmee",
                created_at=datetime.now(UTC),
            ),
        )

    async def record_ride_settlement(self, ride: Ride, *, payment_status: PaymentStatus) -> None:
        if ride.driver_id is None:
            return
        fare = ride.final_fare or ride.estimated_fare
        if fare is None:
            return
        commission = ride.platform_commission
        payout = ride.driver_payout_estimate
        if commission is None or payout is None:
            return

        if ride.payment_method.value == PaymentMethod.CASH.value and payment_status is PaymentStatus.COLLECTED:
            await self.payment_repo.record_ledger_entry_once(
                DriverLedgerEntry(
                    id=DriverLedgerEntry.new_id(),
                    driver_id=ride.driver_id,
                    amount=commission,
                    currency=ride.currency,
                    direction=WalletEntryDirection.DEBIT,
                    entry_type=WalletEntryType.PLATFORM_COMMISSION,
                    status=WalletEntryStatus.CONFIRMED,
                    reference_type="ride",
                    reference_id=ride.id,
                    description="Commission DiddiGo sur course cash",
                    created_at=datetime.now(UTC),
                ),
            )
            return

        if ride.payment_method.value in {PaymentMethod.DIDDIPAY.value, PaymentMethod.WAVE.value}:
            if payment_status is not PaymentStatus.SUCCEEDED:
                return
            await self.payment_repo.record_ledger_entry_once(
                DriverLedgerEntry(
                    id=DriverLedgerEntry.new_id(),
                    driver_id=ride.driver_id,
                    amount=payout,
                    currency=ride.currency,
                    direction=WalletEntryDirection.CREDIT,
                    entry_type=WalletEntryType.RIDE_PAYOUT,
                    status=WalletEntryStatus.CONFIRMED,
                    reference_type="ride",
                    reference_id=ride.id,
                    description="Montant net chauffeur sur course digitale",
                    created_at=datetime.now(UTC),
                ),
            )

    async def _driver_id_for_user(self, user_id: UUID) -> UUID:
        profile = await self.driver_repo.find_by_user_id(user_id)
        if profile is None:
            raise ApiError(404, ErrorCode.DRIVER_PROFILE_NOT_FOUND, "Aucun profil chauffeur pour ce compte.")
        return profile.id

    async def _require_driver(self, driver_id: UUID) -> None:
        profile = await self.driver_repo.find_by_id(driver_id)
        if profile is None:
            raise ApiError(404, ErrorCode.DRIVER_PROFILE_NOT_FOUND, "Aucun profil chauffeur pour cet identifiant.")


def _payment_status_from_diddipay(status: str) -> PaymentStatus:
    try:
        return PaymentStatus(status or PaymentStatus.REQUIRES_ACTION.value)
    except ValueError as exc:
        raise ApiError(422, ErrorCode.PAYMENT_STATUS_INVALID, "Statut DiddiPay non reconnu.", {"status": status}) from exc


def _topup_status_from_payment_status(status: PaymentStatus) -> TopupStatus:
    mapping = {
        PaymentStatus.PENDING: TopupStatus.PENDING,
        PaymentStatus.REQUIRES_ACTION: TopupStatus.REQUIRES_ACTION,
        PaymentStatus.PROCESSING: TopupStatus.PROCESSING,
        PaymentStatus.SUCCEEDED: TopupStatus.SUCCEEDED,
        PaymentStatus.FAILED: TopupStatus.FAILED,
        PaymentStatus.CANCELLED: TopupStatus.CANCELLED,
    }
    return mapping.get(status, TopupStatus.FAILED)


def _wallet_payload(wallet, *, min_balance: Decimal) -> dict:
    return {
        "driver_id": str(wallet.driver_id),
        "balance": int(wallet.balance),
        "currency": wallet.currency,
        "min_balance": int(min_balance),
        "can_go_online": wallet.balance >= min_balance,
    }


def _ledger_payload(entry: DriverLedgerEntry) -> dict:
    return {
        "id": str(entry.id),
        "driver_id": str(entry.driver_id),
        "amount": int(entry.amount),
        "currency": entry.currency,
        "direction": entry.direction.value,
        "type": entry.entry_type.value,
        "status": entry.status.value,
        "reference_type": entry.reference_type,
        "reference_id": str(entry.reference_id),
        "description": entry.description,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


def _topup_payload(topup: DriverTopup, *, next_action: dict | None) -> dict:
    return {
        "id": str(topup.id),
        "driver_id": str(topup.driver_id),
        "amount": int(topup.amount),
        "currency": topup.currency,
        "method": topup.method.value,
        "status": topup.status.value,
        "provider": "diddipay",
        "provider_status": topup.provider_status,
        "payment_intent_id": str(topup.payment_intent_id) if topup.payment_intent_id else None,
        "business_reference": topup.business_reference,
        "paid_at": topup.paid_at.isoformat() if topup.paid_at else None,
        "next_action": next_action,
    }


def _next_action_from_intent(intent: dict) -> dict | None:
    attempts = intent.get("attempts") if isinstance(intent.get("attempts"), list) else []
    if not attempts or not isinstance(attempts[0], dict):
        return None
    next_action = attempts[0].get("next_action")
    return next_action if isinstance(next_action, dict) else None
