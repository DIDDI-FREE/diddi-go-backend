"""One-time back-fill: tell DiddiFreeID the real approval date of every active driver (ticket 084).

Drivers DiddiGo approved before ticket 084 are still `requested` in DiddiFreeID, with no
first validation date. This script queues one `enabled` status per active driver with
his real approval date; the `capability-projection` worker sends them to DiddiFreeID.

    python -m app_base.tools.backfill_driver_access_status            # dry run (default): lists, changes nothing
    python -m app_base.tools.backfill_driver_access_status --apply    # queues the statuses
    python -m app_base.tools.backfill_driver_access_status --apply --include-recent

Date used, best first:
  1. first approval in the KYC review history (every required document approved);
  2. `license_verified_at` (last approval);
  3. `kyc_reviewed_at` (last review);
  4. the driver's creation date in DiddiGo.
Drivers whose date is on or after 2026-11-25 are real newcomers: listed, but queued only
with --include-recent (the PM expects every back-filled date before that day).

Running it twice queues nothing new for drivers already back-filled. Ids only are printed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime

from sqlalchemy import select

from app_base.core.database import async_session_factory
from app_base.modules.ride.application.driver_service import KYC_DOCUMENT_TYPES
from app_base.modules.ride.domain.driver_access import ENABLED, first_approval_from_history
from app_base.modules.ride.infra import models as orm
from app_base.modules.ride.infra.driver_access_repository import SqlAlchemyDriverAccessStatusRepository

NEWCOMER_FROM = datetime(2026, 11, 25, tzinfo=UTC)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def approval_date(row: orm.DriverProfileModel) -> tuple[datetime, str]:
    """(date, where it comes from) for one active driver."""
    first = first_approval_from_history(row.kyc_review_history, required_documents=set(KYC_DOCUMENT_TYPES))
    if first is not None:
        return first, "first_approval_in_history"
    for value, source in (
        (row.license_verified_at, "last_approval_date"),
        (row.kyc_reviewed_at, "last_review_date"),
        (row.created_at, "driver_created_at"),
    ):
        if value is not None:
            return _aware(value), source
    return datetime.now(UTC), "none_found"


async def run(*, apply: bool, include_recent: bool) -> dict:
    report = {"apply": apply, "drivers": [], "counts": {}}
    async with async_session_factory() as session:
        repository = SqlAlchemyDriverAccessStatusRepository(session)
        rows = (
            await session.execute(
                select(orm.DriverProfileModel)
                .where(orm.DriverProfileModel.status == "active")
                .order_by(orm.DriverProfileModel.created_at)
            )
        ).scalars().all()
        for row in rows:
            date, source = approval_date(row)
            recent = date >= NEWCOMER_FROM
            already = await repository.has_backfill(row.user_id)
            action = "skip_already_backfilled" if already else (
                "skip_recent" if recent and not include_recent else "queue"
            )
            if apply and action == "queue":
                await repository.enqueue(
                    user_id=row.user_id, access_status=ENABLED, reason="backfill_existing_driver",
                    source="backfill", now=datetime.now(UTC), enabled_at=date,
                )
            report["drivers"].append({
                "driver_id": str(row.id), "user_id": str(row.user_id), "enabled_at": date.isoformat(),
                "date_source": source, "on_or_after_2026_11_25": recent, "action": action,
            })
            report["counts"][source] = report["counts"].get(source, 0) + 1
            report["counts"][action] = report["counts"].get(action, 0) + 1
        if apply:
            await session.commit()
        else:
            await session.rollback()
    report["counts"]["active_drivers"] = len(report["drivers"])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Back-fill driver approval dates into DiddiFreeID (ticket 084).")
    parser.add_argument("--apply", action="store_true", help="queue the statuses (default: dry run)")
    parser.add_argument(
        "--include-recent", action="store_true",
        help="also queue drivers approved on or after 2026-11-25 (real newcomers)",
    )
    parser.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = parser.parse_args()
    report = asyncio.run(run(apply=args.apply, include_recent=args.include_recent))
    if args.json:
        print(json.dumps(report, indent=2))
        return
    print("DRY RUN, nothing changed" if not args.apply else "APPLIED, statuses queued")
    print(f"{'driver_id':36}  {'user_id':36}  {'enabled_at':32}  {'date_source':26}  action")
    for item in report["drivers"]:
        print(
            f"{item['driver_id']:36}  {item['user_id']:36}  {item['enabled_at']:32}  "
            f"{item['date_source']:26}  {item['action']}"
        )
    print("counts:", json.dumps(report["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
