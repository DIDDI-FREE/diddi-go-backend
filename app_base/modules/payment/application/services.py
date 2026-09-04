"""Payment use cases for DiddiGo.

Cash remains local to DiddiGo. Digital collection goes through DiddiPay's
PaymentIntent contract; DiddiGo stores only its local payment link/status.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.core.settings import settings
from app_base.modules.payment.domain.entities import (
    KEEP,
    DriverLedgerEntry,
    DriverTopup,
    PaymentMethod,
    PaymentStatus,
    TopupStatus,
    Transaction,
    WalletEntryDirection,
    WalletEntryStatus,
    WalletEntryType,
)
from app_base.modules.payment.domain.interfaces import PaymentRepository
from app_base.modules.payment.infra.diddipay_client import DiddiPayClient
from app_base.modules.ride.domain.entities import RideStatus
from app_base.modules.ride.domain.interfaces import RideRepository

logger = logging.getLogger(__name__)

_ABSOLUTE_TOLERANCE = Decimal("200")
_RELATIVE_TOLERANCE = Decimal("0.10")


@dataclass
class ReconciliationReport:
    """Outcome of one reconciliation sweep — logged and returned to admins."""

    checked: int = 0
    updated: int = 0
    unchanged: int = 0
    missing: int = 0
    mismatched: int = 0
    errors: int = 0
    updated_references: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "checked": self.checked,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "missing": self.missing,
            "mismatched": self.mismatched,
            "errors": self.errors,
            "updated_references": self.updated_references,
        }


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
        log_event(
            "payment.cash.confirmed",
            ride_id=ride_id,
            payment_id=payment.id,
            collected_by=collected_by,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status.value,
        )
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

        log_event("payment.prepare.started", ride_id=ride_id, payer_user_id=payer_user_id, method=payment_method.value)
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
            log_event("payment.webhook.duplicate", event_id=event_id, payment_intent_id=intent_id)
            return {"status": "duplicate"}
        if intent_id is None:
            raise ApiError(422, ErrorCode.PAYMENT_CALLBACK_INVALID, "PaymentIntent ID manquant.")

        status = _payment_status_from_diddipay(str(data.get("status") or ""))
        paid_at = datetime.now(UTC) if status is PaymentStatus.SUCCEEDED else None
        payment = await self.payment_repo.find_by_payment_intent_id(intent_id)
        if payment is not None:
            if int(data.get("amount") or -1) != int(payment.amount) or data.get("currency") != payment.currency:
                raise ApiError(409, ErrorCode.PAYMENT_OPERATION_CONFLICT, "Montant ou devise DiddiPay incoherent.")
            if data.get("business_reference") != payment.business_reference:
                raise ApiError(409, ErrorCode.PAYMENT_OPERATION_CONFLICT, "Reference metier DiddiPay incoherente.")

            await self._apply_transaction_status(
                payment,
                status=status,
                provider_status=str(data.get("status") or ""),
                paid_at=paid_at,
            )
            log_event(
                "payment.webhook.processed",
                event_id=event_id,
                payment_intent_id=intent_id,
                reference_type="ride",
                status=status.value,
            )
            return {"status": "processed", "payment_intent_id": str(intent_id), "reference_type": "ride"}

        topup = await self.payment_repo.find_topup_by_payment_intent_id(intent_id)
        if topup is None:
            raise ApiError(404, ErrorCode.PAYMENT_INTENT_NOT_FOUND, "Paiement DiddiGo introuvable.")
        if int(data.get("amount") or -1) != int(topup.amount) or data.get("currency") != topup.currency:
            raise ApiError(409, ErrorCode.PAYMENT_OPERATION_CONFLICT, "Montant ou devise DiddiPay incoherent.")
        if data.get("business_reference") != topup.business_reference:
            raise ApiError(409, ErrorCode.PAYMENT_OPERATION_CONFLICT, "Reference metier DiddiPay incoherente.")

        await self._apply_topup_status(
            topup,
            status=_topup_status_from_payment_status(status),
            provider_status=str(data.get("status") or ""),
            paid_at=paid_at,
        )
        log_event(
            "payment.webhook.processed",
            event_id=event_id,
            payment_intent_id=intent_id,
            reference_type="driver_topup",
            status=status.value,
        )
        return {"status": "processed", "payment_intent_id": str(intent_id), "reference_type": "driver_topup"}

    # --- reconciliation ----------------------------------------------------
    #
    # Callbacks get lost: DiddiGo can be redeploying when DiddiPay fires, the
    # HMAC secret can be rotated mid-flight, the network can drop the POST. The
    # sweep below re-reads GET /payment-intents/{id} — DiddiPay is the source of
    # truth — and replays the exact same state transition the webhook would
    # have. Every effect it triggers (wallet credit, driver settlement) is
    # guarded by the ledger's uniqueness constraint, so a payment already
    # settled by its callback is a no-op here.

    async def reconcile_pending(
        self,
        *,
        limit: int | None = None,
        min_age_seconds: int | None = None,
        max_age_seconds: int | None = None,
    ) -> ReconciliationReport:
        """Re-read every intent still awaiting a callback and apply its state.

        `min_age_seconds` leaves freshly created intents alone — the passenger
        may still be on the checkout page and the callback is simply not due
        yet. `max_age_seconds` stops the job from chasing intents so old that
        DiddiPay has already expired them.
        """
        limit = limit if limit is not None else settings.payment_reconciliation_batch_size
        min_age = min_age_seconds if min_age_seconds is not None else settings.payment_reconciliation_min_age_seconds
        max_age = max_age_seconds if max_age_seconds is not None else settings.payment_reconciliation_max_age_seconds

        now = datetime.now(UTC)
        created_before = now - timedelta(seconds=min_age)
        created_after = now - timedelta(seconds=max_age)
        report = ReconciliationReport()

        transactions = await self.payment_repo.list_stale_transactions(
            created_before=created_before,
            created_after=created_after,
            limit=limit,
        )
        for payment in transactions:
            await self._reconcile_transaction(payment, report)

        topups = await self.payment_repo.list_stale_topups(
            created_before=created_before,
            created_after=created_after,
            limit=limit,
        )
        for topup in topups:
            await self._reconcile_topup(topup, report)

        return report

    async def reconcile_transaction(self, ride_id: UUID) -> ReconciliationReport:
        """Reconcile a single ride payment on demand (admin repair path)."""
        report = ReconciliationReport()
        payment = await self.payment_repo.find_by_ride_id(ride_id)
        if payment is None or payment.payment_intent_id is None:
            raise ApiError(404, ErrorCode.PAYMENT_INTENT_NOT_FOUND, "Aucun paiement DiddiPay pour cette course.")
        await self._reconcile_transaction(payment, report)
        return report

    async def reconcile_topup(self, topup_id: UUID) -> ReconciliationReport:
        """Reconcile a single driver topup on demand (admin repair path)."""
        report = ReconciliationReport()
        topup = await self.payment_repo.find_topup_by_id(topup_id)
        if topup is None or topup.payment_intent_id is None:
            raise ApiError(404, ErrorCode.PAYMENT_INTENT_NOT_FOUND, "Aucune recharge DiddiPay pour cet identifiant.")
        await self._reconcile_topup(topup, report)
        return report

    async def _reconcile_transaction(self, payment: Transaction, report: ReconciliationReport) -> None:
        reference = payment.business_reference or f"diddigo:ride:{payment.ride_id}"
        report.checked += 1
        intent = await self._read_intent(payment.payment_intent_id, reference, report)
        if intent is None:
            return

        mismatch = _intent_mismatch_reason(
            intent,
            amount=payment.amount,
            currency=payment.currency,
            business_reference=payment.business_reference,
        )
        if mismatch is not None:
            report.mismatched += 1
            logger.error(
                "reconciliation refused %s (%s) intent=%s local=%s%s provider=%s%s",
                reference,
                mismatch,
                payment.payment_intent_id,
                int(payment.amount),
                payment.currency,
                intent.get("amount"),
                intent.get("currency"),
            )
            return

        provider_status = str(intent.get("status") or "")
        try:
            status = _payment_status_from_diddipay(provider_status)
        except ApiError:
            report.errors += 1
            logger.exception("reconciliation got an unknown DiddiPay status reference=%s", reference)
            return

        next_action = _next_action_from_intent(intent)
        if status is payment.status and next_action == payment.provider_next_action:
            report.unchanged += 1
            return

        await self._apply_transaction_status(
            payment,
            status=status,
            provider_status=provider_status,
            paid_at=datetime.now(UTC) if status is PaymentStatus.SUCCEEDED else None,
            next_action=next_action,
        )
        report.updated += 1
        report.updated_references.append(reference)
        logger.info(
            "reconciliation repaired reference=%s intent=%s %s -> %s",
            reference,
            payment.payment_intent_id,
            payment.status.value,
            status.value,
        )

    async def _reconcile_topup(self, topup: DriverTopup, report: ReconciliationReport) -> None:
        reference = topup.business_reference or f"diddigo:driver_topup:{topup.id}"
        report.checked += 1
        intent = await self._read_intent(topup.payment_intent_id, reference, report)
        if intent is None:
            return

        mismatch = _intent_mismatch_reason(
            intent,
            amount=topup.amount,
            currency=topup.currency,
            business_reference=topup.business_reference,
        )
        if mismatch is not None:
            report.mismatched += 1
            logger.error(
                "reconciliation refused %s (%s) intent=%s local=%s%s provider=%s%s",
                reference,
                mismatch,
                topup.payment_intent_id,
                int(topup.amount),
                topup.currency,
                intent.get("amount"),
                intent.get("currency"),
            )
            return

        provider_status = str(intent.get("status") or "")
        try:
            status = _topup_status_from_payment_status(_payment_status_from_diddipay(provider_status))
        except ApiError:
            report.errors += 1
            logger.exception("reconciliation got an unknown DiddiPay status reference=%s", reference)
            return

        next_action = _next_action_from_intent(intent)
        if status is topup.status and next_action == topup.provider_next_action:
            report.unchanged += 1
            return

        await self._apply_topup_status(
            topup,
            status=status,
            provider_status=provider_status,
            paid_at=datetime.now(UTC) if status is TopupStatus.SUCCEEDED else None,
            next_action=next_action,
        )
        report.updated += 1
        report.updated_references.append(reference)
        logger.info(
            "reconciliation repaired reference=%s intent=%s %s -> %s",
            reference,
            topup.payment_intent_id,
            topup.status.value,
            status.value,
        )

    async def _read_intent(
        self,
        payment_intent_id: UUID | None,
        reference: str,
        report: ReconciliationReport,
    ) -> dict | None:
        """Fetch one intent, converting any failure into a counted outcome.

        A sweep must survive a single bad row: one 5xx from DiddiPay cannot be
        allowed to abandon the rest of the batch.
        """
        if payment_intent_id is None:
            report.missing += 1
            return None
        try:
            intent = await (self.diddipay or DiddiPayClient()).get_payment_intent(payment_intent_id)
        except Exception:
            report.errors += 1
            logger.exception(
                "reconciliation could not read intent reference=%s intent=%s",
                reference,
                payment_intent_id,
            )
            return None
        if intent is None:
            report.missing += 1
            logger.error(
                "reconciliation found no DiddiPay intent reference=%s intent=%s",
                reference,
                payment_intent_id,
            )
        return intent

    async def _apply_transaction_status(
        self,
        payment: Transaction,
        *,
        status: PaymentStatus,
        provider_status: str,
        paid_at: datetime | None,
        next_action: object = KEEP,
    ) -> Transaction:
        payment = await self.payment_repo.mark_external_status(
            payment.id,
            status,
            provider_status=provider_status,
            paid_at=paid_at,
            next_action=next_action,
        )
        ride = await self.ride_repo.find_by_id(payment.ride_id)
        if ride is not None:
            await self._record_ride_settlement(ride, payment.status)
        return payment

    async def _apply_topup_status(
        self,
        topup: DriverTopup,
        *,
        status: TopupStatus,
        provider_status: str,
        paid_at: datetime | None,
        next_action: object = KEEP,
    ) -> DriverTopup:
        topup = await self.payment_repo.mark_topup_status(
            topup.id,
            status,
            provider_status=provider_status,
            paid_at=paid_at,
            next_action=next_action,
        )
        if topup.status is TopupStatus.SUCCEEDED:
            await self._credit_driver_topup(topup)
        return topup

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
            log_event(
                "payment.prepare.reused",
                ride_id=ride_id,
                payment_id=existing.id,
                payment_intent_id=existing.payment_intent_id,
                status=existing.status.value,
            )
            return _external_payment_payload(existing, next_action=existing.provider_next_action)
        if existing:
            raise ApiError(
                409,
                ErrorCode.PAYMENT_OPERATION_CONFLICT,
                "Une transaction locale existe deja pour cette course.",
            )

        idempotency_key = f"diddigo:ride:{ride_id}:collection:v1"
        business_reference = f"diddigo:ride:{ride_id}"
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
        next_action = _next_action_from_intent(intent)
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
            provider_next_action=next_action,
            paid_at=datetime.now(UTC) if status is PaymentStatus.SUCCEEDED else None,
        )
        await self.payment_repo.save(payment)
        log_event(
            "payment.prepare.created",
            ride_id=ride_id,
            payment_id=payment.id,
            payment_intent_id=payment.payment_intent_id,
            method=payment_method.value,
            amount=payment.amount,
            currency=payment.currency,
            provider_status=payment.provider_status,
            has_next_action=next_action is not None,
        )
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
        is_digital_payment = ride.payment_method.value in {PaymentMethod.DIDDIPAY.value, PaymentMethod.WAVE.value}
        if is_digital_payment and payment_status is PaymentStatus.SUCCEEDED:
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


def _intent_mismatch_reason(
    intent: dict,
    *,
    amount: Decimal,
    currency: str,
    business_reference: str | None,
) -> str | None:
    """Refuse to move a local row unless the intent is unambiguously the same money.

    An absent field is reported separately from a differing one: the first
    means DiddiPay's read model doesn't carry what we compare on (a contract
    problem to fix), the second means the intent genuinely isn't ours.
    """
    if intent.get("amount") is None or intent.get("currency") is None:
        return "provider response carries no amount/currency to verify against"
    try:
        provider_amount = int(intent["amount"])
    except (TypeError, ValueError):
        return "provider amount is not a number"
    if provider_amount != int(amount) or str(intent["currency"]) != currency:
        return "provider amount/currency differs from the local record"
    if business_reference and intent.get("business_reference") not in {None, business_reference}:
        return "provider business_reference differs from the local record"
    return None


def _next_action_from_intent(intent: dict) -> dict | None:
    attempts = intent.get("attempts") if isinstance(intent.get("attempts"), list) else []
    if not attempts or not isinstance(attempts[0], dict):
        return None
    next_action = attempts[0].get("next_action")
    return next_action if isinstance(next_action, dict) else None
