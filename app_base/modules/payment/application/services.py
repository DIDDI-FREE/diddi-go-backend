"""Payment use cases for DiddiGo.

Cash remains local to DiddiGo. Digital collection goes through DiddiPay's
PaymentIntent contract; DiddiGo stores only its local payment link/status.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.settings import settings
from app_base.modules.payment.domain.entities import (
    DriverLedgerEntry,
    PaymentMethod,
    PaymentStatus,
    TopupStatus,
    WalletEntryDirection,
    WalletEntryStatus,
    WalletEntryType,
    Transaction,
)
from app_base.modules.payment.domain.interfaces import PaymentRepository
from app_base.modules.payment.infra.diddipay_client import DiddiPayClient
from app_base.modules.ride.domain.entities import RideStatus
from app_base.modules.ride.domain.interfaces import RideRepository

_ABSOLUTE_TOLERANCE = Decimal("200")
_RELATIVE_TOLERANCE = Decimal("0.10")


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class PaymentService:
    payment_repo: PaymentRepository
    ride_repo: RideRepository
    diddipay: DiddiPayClient | None = None

    async def confirm_cash(
        self,
        ride_id: UUID,
        amount_collected: Decimal,
        *,
        collected_by: UUID,
    ) -> dict:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, ErrorCode.RIDE_NOT_FOUND, "Aucune course trouvee avec cet identifiant.")
        if ride.status != RideStatus.COMPLETED:
            raise ApiError(409, ErrorCode.RIDE_NOT_COMPLETED, "Impossible de confirmer un paiement avant la fin.")

        expected = ride.final_fare
        if expected is not None:
            tolerance = max(_ABSOLUTE_TOLERANCE, expected * _RELATIVE_TOLERANCE)
            if abs(amount_collected - expected) > tolerance:
                raise ApiError(422, "AMOUNT_MISMATCH", "Le montant encaisse ne correspond pas au montant final.")

        now = datetime.now(UTC)
        payment = await self.payment_repo.find_by_ride_id(ride_id)
        if payment is None:
            payment = Transaction(
                id=Transaction.new_id(),
                ride_id=ride_id,
                amount=amount_collected,
                currency=ride.currency,
                method=PaymentMethod.CASH,
                status=PaymentStatus.PENDING,
                created_at=now,
            )
            await self.payment_repo.save(payment)

        payment = await self.payment_repo.update_collected(
            transaction_id=payment.id,
            collected_by=collected_by,
            amount=amount_collected,
            collected_at=now,
        )
        await self._record_ride_settlement(ride, payment.status)
        return {
            "ride_id": str(payment.ride_id),
            "status": payment.status.value,
            "amount": int(payment.amount),
            "currency": payment.currency,
            "collected_at": _iso(payment.collected_at),
        }

    async def get_payment(self, ride_id: UUID) -> dict:
        payment = await self.payment_repo.find_by_ride_id(ride_id)
        if payment is None:
            ride = await self.ride_repo.find_by_id(ride_id)
            method = ride.payment_method.value if ride is not None else "cash"
            return {"ride_id": str(ride_id), "status": "pending", "method": method, "amount": None, "currency": "XOF"}
        payload = {
            "ride_id": str(payment.ride_id),
            "status": payment.status.value,
            "method": payment.method.value,
            "amount": int(payment.amount),
            "currency": payment.currency,
        }
        if payment.payment_intent_id:
            payload.update(
                {
                    "provider": "diddipay",
                    "provider_status": payment.provider_status,
                    "payment_intent_id": str(payment.payment_intent_id),
                    "business_reference": payment.business_reference,
                    "paid_at": _iso(payment.paid_at),
                }
            )
        return payload

    async def prepare_payment(
        self,
        ride_id: UUID,
        method: str,
        *,
        payer_user_id: UUID,
        customer_email: str | None = None,
        customer_phone: str | None = None,
        callback_url: str | None = None,
    ) -> dict:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, ErrorCode.RIDE_NOT_FOUND, "Aucune course trouvee avec cet identifiant.")
        if ride.passenger_user_id != payer_user_id:
            raise ApiError(403, ErrorCode.RIDE_NOT_OWNED_BY_USER, "Cette course ne vous appartient pas.")
        try:
            payment_method = PaymentMethod(method)
        except ValueError as exc:
            raise ApiError(422, ErrorCode.INVALID_PAYMENT_METHOD, "Methode de paiement invalide.") from exc

        if payment_method is PaymentMethod.CASH:
            return await self._prepare_cash(ride_id)

        if not customer_email:
            raise ApiError(
                422,
                ErrorCode.PAYMENT_EMAIL_REQUIRED,
                "Un email client est requis pour initialiser un paiement DiddiPay/Paystack.",
                {"field": "customer_email"},
            )
        return await self._prepare_diddipay(
            ride_id,
            payment_method,
            payer_user_id=payer_user_id,
            customer_email=customer_email,
            customer_phone=customer_phone,
            callback_url=callback_url,
        )

    async def apply_diddipay_webhook(
        self,
        *,
        raw_body: bytes,
        event_id_header: str | None,
        signature: str | None,
    ) -> dict:
        if not settings.diddipay_callback_secret:
            raise ApiError(503, ErrorCode.PAYMENT_CONFIGURATION_MISSING, "Secret callback DiddiPay non configure.")
        expected = hmac.new(settings.diddipay_callback_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(signature, expected):
            raise ApiError(401, ErrorCode.PAYMENT_CALLBACK_INVALID, "Signature callback DiddiPay invalide.")

        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ApiError(422, ErrorCode.PAYMENT_CALLBACK_INVALID, "Payload callback DiddiPay invalide.") from exc

        event_id = str(payload.get("id") or "")
        if not event_id or event_id_header != event_id:
            raise ApiError(422, ErrorCode.PAYMENT_CALLBACK_INVALID, "Event ID DiddiPay invalide.")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ApiError(422, ErrorCode.PAYMENT_CALLBACK_INVALID, "Donnees callback DiddiPay manquantes.")

        intent_id = UUID(str(data["payment_intent_id"])) if data.get("payment_intent_id") else None
        stored = await self.payment_repo.record_webhook_event(
            event_id=event_id,
            payment_intent_id=intent_id,
            event_type=str(payload.get("type") or ""),
            business_reference=data.get("business_reference"),
            payload=raw_body.decode("utf-8"),
        )
        if not stored:
            return {"status": "duplicate"}
        if intent_id is None:
            raise ApiError(422, ErrorCode.PAYMENT_CALLBACK_INVALID, "PaymentIntent ID manquant.")

        status = _payment_status_from_diddipay(str(data.get("status") or ""))
        paid_at = datetime.now(UTC) if status is PaymentStatus.SUCCEEDED else None
        payment = await self.payment_repo.find_by_payment_intent_id(intent_id)
        if payment is not None:
            if int(data.get("amount") or -1) != int(payment.amount) or data.get("currency") != payment.currency:
                raise ApiError(409, ErrorCode.PAYMENT_OPERATION_CONFLICT, "Montant ou devise DiddiPay incoherent.")

            payment = await self.payment_repo.mark_external_status(
                payment.id,
                status,
                provider_status=str(data.get("status") or ""),
                paid_at=paid_at,
            )
            ride = await self.ride_repo.find_by_id(payment.ride_id)
            if ride is not None:
                await self._record_ride_settlement(ride, payment.status)
            return {"status": "processed", "payment_intent_id": str(intent_id), "reference_type": "ride"}

        topup = await self.payment_repo.find_topup_by_payment_intent_id(intent_id)
        if topup is None:
            raise ApiError(404, ErrorCode.PAYMENT_INTENT_NOT_FOUND, "Paiement DiddiGo introuvable.")
        if int(data.get("amount") or -1) != int(topup.amount) or data.get("currency") != topup.currency:
            raise ApiError(409, ErrorCode.PAYMENT_OPERATION_CONFLICT, "Montant ou devise DiddiPay incoherent.")

        topup_status = _topup_status_from_payment_status(status)
        topup = await self.payment_repo.mark_topup_status(
            topup.id,
            topup_status,
            provider_status=str(data.get("status") or ""),
            paid_at=paid_at,
        )
        if topup.status is TopupStatus.SUCCEEDED:
            await self._credit_driver_topup(topup)
        return {"status": "processed", "payment_intent_id": str(intent_id), "reference_type": "driver_topup"}

    async def _prepare_cash(self, ride_id: UUID) -> dict:
        payment = await self.payment_repo.find_by_ride_id(ride_id)
        if payment is None:
            ride = await self.ride_repo.find_by_id(ride_id)
            if ride is None:
                raise ApiError(404, ErrorCode.RIDE_NOT_FOUND, "Aucune course trouvee avec cet identifiant.")
            payment = Transaction(
                id=Transaction.new_id(),
                ride_id=ride_id,
                amount=ride.final_fare or ride.estimated_fare or Decimal("0"),
                currency=ride.currency,
                method=PaymentMethod.CASH,
                status=PaymentStatus.PENDING,
                created_at=datetime.now(UTC),
            )
            await self.payment_repo.save(payment)
        return {
            "ride_id": str(payment.ride_id),
            "status": payment.status.value,
            "method": payment.method.value,
            "amount": int(payment.amount),
            "currency": payment.currency,
            "provider": "cash",
            "provider_status": "local",
        }

    async def _prepare_diddipay(
        self,
        ride_id: UUID,
        payment_method: PaymentMethod,
        *,
        payer_user_id: UUID,
        customer_email: str,
        customer_phone: str | None,
        callback_url: str | None,
    ) -> dict:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, ErrorCode.RIDE_NOT_FOUND, "Aucune course trouvee avec cet identifiant.")
        amount = ride.final_fare or ride.estimated_fare
        if amount is None or amount <= 0:
            raise ApiError(409, ErrorCode.PAYMENT_OPERATION_CONFLICT, "Montant de course indisponible.")

        existing = await self.payment_repo.find_by_ride_id(ride_id)
        if existing and existing.payment_intent_id:
            return _external_payment_payload(existing, next_action=None)
        if existing:
            raise ApiError(
                409,
                ErrorCode.PAYMENT_OPERATION_CONFLICT,
                "Une transaction locale existe deja pour cette course.",
            )

        idempotency_key = f"ride:{ride_id}:collection:v1"
        business_reference = f"ride:{ride_id}"
        intent = await (self.diddipay or DiddiPayClient()).create_payment_intent(
            {
                "business_reference": business_reference,
                "amount": int(amount),
                "currency": ride.currency,
                "payer_user_id": str(payer_user_id),
                "payee_user_id": str(ride.driver_id) if ride.driver_id else None,
                "channel": "mobile_money",
                "network": "wave" if payment_method is PaymentMethod.WAVE else None,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "callback_url": callback_url or settings.diddigo_payment_callback_url,
                "description": f"Course DiddiGo {ride_id}",
                "metadata": {"ride_id": str(ride_id)},
            },
            idempotency_key=idempotency_key,
        )
        status = _payment_status_from_diddipay(str(intent.get("status") or "requires_action"))
        payment = Transaction(
            id=Transaction.new_id(),
            ride_id=ride_id,
            amount=Decimal(str(intent.get("amount") or amount)),
            currency=str(intent.get("currency") or ride.currency),
            method=payment_method,
            status=status,
            created_at=datetime.now(UTC),
            payment_intent_id=UUID(str(intent["id"])),
            business_reference=business_reference,
            idempotency_key=idempotency_key,
            provider_status=str(intent.get("status") or status.value),
            paid_at=datetime.now(UTC) if status is PaymentStatus.SUCCEEDED else None,
        )
        await self.payment_repo.save(payment)
        attempts = intent.get("attempts") if isinstance(intent.get("attempts"), list) else []
        next_action = attempts[0].get("next_action") if attempts and isinstance(attempts[0], dict) else None
        return _external_payment_payload(payment, next_action=next_action)

    async def _record_ride_settlement(self, ride, payment_status: PaymentStatus) -> None:
        if ride.driver_id is None:
            return
        if ride.platform_commission is None or ride.driver_payout_estimate is None:
            return
        if ride.payment_method.value == PaymentMethod.CASH.value and payment_status is PaymentStatus.COLLECTED:
            await self.payment_repo.record_ledger_entry_once(
                DriverLedgerEntry(
                    id=DriverLedgerEntry.new_id(),
                    driver_id=ride.driver_id,
                    amount=ride.platform_commission,
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
        if ride.payment_method.value in {PaymentMethod.DIDDIPAY.value, PaymentMethod.WAVE.value} and payment_status is PaymentStatus.SUCCEEDED:
            await self.payment_repo.record_ledger_entry_once(
                DriverLedgerEntry(
                    id=DriverLedgerEntry.new_id(),
                    driver_id=ride.driver_id,
                    amount=ride.driver_payout_estimate,
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

    async def _credit_driver_topup(self, topup) -> None:
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


def _payment_status_from_diddipay(status: str) -> PaymentStatus:
    try:
        return PaymentStatus(status)
    except ValueError as exc:
        raise ApiError(
            422,
            ErrorCode.PAYMENT_STATUS_INVALID,
            "Statut DiddiPay non reconnu.",
            {"status": status},
        ) from exc


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


def _external_payment_payload(payment: Transaction, *, next_action: dict | None) -> dict:
    return {
        "ride_id": str(payment.ride_id),
        "status": payment.status.value,
        "method": payment.method.value,
        "amount": int(payment.amount),
        "currency": payment.currency,
        "provider": "diddipay",
        "provider_status": payment.provider_status,
        "payment_intent_id": str(payment.payment_intent_id) if payment.payment_intent_id else None,
        "business_reference": payment.business_reference,
        "next_action": next_action,
    }
