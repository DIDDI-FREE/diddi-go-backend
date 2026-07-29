"""Payment use cases — DB-backed, cash-only at launch.

Inter-module boundary: payment reads ride state via `RideRepository`,
never via a direct SQL cross-schema query — the architecture doc's most
important rule ("un module ne fait jamais de requête SQL directe sur les
tables d'un autre module").
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app_base.core.errors import ApiError
from app_base.modules.payment.domain.entities import (
    PaymentMethod,
    PaymentStatus,
    Transaction,
)
from app_base.modules.payment.domain.interfaces import PaymentRepository
from app_base.modules.ride.domain.entities import RideStatus
from app_base.modules.ride.domain.interfaces import RideRepository

# Tolerance: collected amount can diverge from the ride's final Fare by
# at most ±10% of expected OR ±200 XOF — whichever is larger. This matches
# the previous in-memory service's tolerance logic.
_ABSOLUTE_TOLERANCE = Decimal("200")
_RELATIVE_TOLERANCE = Decimal("0.10")


def _iso(dt: datetime | None) -> str | None:
    """Render a timestamp as ISO 8601 UTC, per the API contract §0.

    Timestamps read back from PostgreSQL are timezone-aware; ones built in
    process may be naive. A naive value is taken to be UTC (that is how the
    service writes them) rather than silently labelled `Z` while holding
    local time.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class PaymentService:
    payment_repo: PaymentRepository
    ride_repo: RideRepository

    async def confirm_cash(
        self,
        ride_id: UUID,
        amount_collected: Decimal,
        *,
        collected_by: UUID,
    ) -> dict:
        ride = await self.ride_repo.find_by_id(ride_id)
        if ride is None:
            raise ApiError(404, "RIDE_NOT_FOUND", "Aucune course trouvée avec cet identifiant.")
        if ride.status != RideStatus.COMPLETED:
            raise ApiError(409, "RIDE_NOT_COMPLETED", "Impossible de confirmer un paiement avant la fin de course.")

        expected = ride.final_fare
        if expected is not None:
            tolerance = max(_ABSOLUTE_TOLERANCE, expected * _RELATIVE_TOLERANCE)
            if abs(amount_collected - expected) > tolerance:
                raise ApiError(
                    422,
                    "AMOUNT_MISMATCH",
                    "Le montant encaissé ne correspond pas au montant final.",
                )

        now = datetime.utcnow()
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
            return {"ride_id": str(ride_id), "status": "pending", "method": "cash", "amount": None, "currency": "XOF"}
        return {
            "ride_id": str(payment.ride_id),
            "status": payment.status.value,
            "method": payment.method.value,
            "amount": int(payment.amount),
            "currency": payment.currency,
        }
