"""Reconcile DiddiPay payments from the command line.

The API container runs the same sweep on a timer, but a one-shot run is what
you want when a callback was lost during a deploy and a driver is waiting on a
wallet credit right now:

    python -m app_base.tools.reconcile_payments
    python -m app_base.tools.reconcile_payments --topup 4af13b6a-...
    python -m app_base.tools.reconcile_payments --ride 9c1e...  --json

Every path re-reads GET /payfund/v1/payment-intents/{id} and applies the state
DiddiPay reports. All effects are idempotent, so running it twice is safe.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from uuid import UUID

from app_base.core.database import async_session_factory
from app_base.core.settings import settings
from app_base.modules.payment.application.reconciliation import run_reconciliation_once
from app_base.modules.payment.application.services import PaymentService, ReconciliationReport
from app_base.modules.payment.infra.diddipay_client import DiddiPayClient
from app_base.modules.payment.infra.repositories import SqlAlchemyPaymentRepository
from app_base.modules.ride.infra.repositories import SqlAlchemyRideRepository


async def _reconcile_one(*, topup_id: UUID | None, ride_id: UUID | None) -> ReconciliationReport:
    async with async_session_factory() as session:
        service = PaymentService(
            payment_repo=SqlAlchemyPaymentRepository(session),
            ride_repo=SqlAlchemyRideRepository(session),
            diddipay=DiddiPayClient(),
        )
        try:
            if topup_id is not None:
                report = await service.reconcile_topup(topup_id)
            else:
                report = await service.reconcile_transaction(ride_id)  # type: ignore[arg-type]
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    return report


async def _main(args: argparse.Namespace) -> ReconciliationReport:
    if args.topup or args.ride:
        return await _reconcile_one(topup_id=args.topup, ride_id=args.ride)
    return await run_reconciliation_once(limit=args.limit)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile DiddiGo payments against DiddiPay.")
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--topup", type=UUID, help="reconcile a single driver topup id")
    target.add_argument("--ride", type=UUID, help="reconcile the payment of a single ride id")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="max rows per kind for a full sweep (default: PAYMENT_RECONCILIATION_BATCH_SIZE)",
    )
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args()

    if not (settings.diddipay_base_url and settings.diddipay_service_key):
        raise SystemExit("DiddiPay is not configured — set DIDDIPAY_BASE_URL and DIDDIPAY_SERVICE_KEY.")

    report = asyncio.run(_main(args))

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(
            f"checked={report.checked} updated={report.updated} unchanged={report.unchanged} "
            f"missing={report.missing} mismatched={report.mismatched} errors={report.errors}",
        )
        for reference in report.updated_references:
            print(f"  repaired {reference}")

    # Non-zero when something needs a human: an intent DiddiPay does not know,
    # an amount that does not line up, or a provider error we could not read.
    if report.errors or report.mismatched or report.missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
