"""What DiddiFreeID must know about a DiddiGo driver (ticket 084).

DiddiFreeID records, per professional and service, an access status and the date of the
first validation (decision 2026-11-26). DiddiGo derives both from its own driver profile.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app_base.modules.ride.domain.entities import DriverProfile, DriverStatus, KycStatus

ENABLED = "enabled"
SUSPENDED = "suspended"
REJECTED = "rejected"


def access_status(profile: DriverProfile, *, required_documents: set[str]) -> str | None:
    """The DiddiFreeID access status for this driver, or None when there is nothing to say yet.

    - active in DiddiGo: `enabled`;
    - approved at least once, now not active (rejected, or documents resubmitted): `suspended`
      (human, 2026-11-26: he was validated, he is stopped; his first date stays);
    - never approved and rejected: `rejected`;
    - never approved and still waiting: None (DiddiFreeID keeps `requested`).
    """
    if profile.status is DriverStatus.ACTIVE:
        return ENABLED
    if first_approval_at(profile, required_documents=required_documents) is not None:
        return SUSPENDED
    if profile.kyc_status is KycStatus.REJECTED:
        return REJECTED
    return None


def first_approval_at(profile: DriverProfile, *, required_documents: set[str]) -> datetime | None:
    """The first time every required KYC document was approved, read from the review history.

    The history keeps every document decision with its date, so it survives later
    rejections and resubmissions, unlike `kyc_reviewed_at` and `license_verified_at`.
    """
    return first_approval_from_history(profile.kyc_review_history, required_documents=required_documents)


def first_approval_from_history(history: list | None, *, required_documents: set[str]) -> datetime | None:
    approved: set[str] = set()
    entries = [entry for entry in (history or []) if isinstance(entry, dict)]
    for entry in sorted(entries, key=lambda item: str(item.get("reviewed_at") or "")):
        document_type = entry.get("document_type")
        when = _parse(entry.get("reviewed_at"))
        if document_type is None or when is None:
            continue
        if entry.get("status") == "approved":
            approved.add(document_type)
        else:
            approved.discard(document_type)
        if required_documents <= approved:
            return when
    return None


def _parse(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
