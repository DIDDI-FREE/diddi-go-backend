"""Canonical service-to-service permissions owned by DiddiGo."""

from __future__ import annotations

DIDDIGO_AUDIENCE = "diddigo"

DRIVERS_READ = "diddigo:drivers:read"
DRIVERS_WRITE = "diddigo:drivers:write"
KYC_READ = "diddigo:kyc:read"
KYC_DECIDE = "diddigo:kyc:decide"
RIDES_READ = "diddigo:rides:read"
RIDES_CANCEL = "diddigo:rides:cancel"
WALLETS_READ = "diddigo:wallets:read"
PAYMENTS_READ = "diddigo:payments:read"
PAYMENTS_RECONCILE = "diddigo:payments:reconcile"
PARTNERS_READ = "diddigo:partners:read"
PARTNERS_WRITE = "diddigo:partners:write"
OPERATIONS_READ = "diddigo:operations:read"
RIDE_SUMMARY_READ = "diddigo:ride-summary:read"

KNOWN_SCOPES = frozenset(
    {
        DRIVERS_READ,
        DRIVERS_WRITE,
        KYC_READ,
        KYC_DECIDE,
        RIDES_READ,
        RIDES_CANCEL,
        WALLETS_READ,
        PAYMENTS_READ,
        PAYMENTS_RECONCILE,
        PARTNERS_READ,
        PARTNERS_WRITE,
        OPERATIONS_READ,
        RIDE_SUMMARY_READ,
    }
)

# Remove after all Pilotage clients have migrated to the namespaced scope.
LEGACY_SCOPE_ALIASES = {"ride-summary:read": RIDE_SUMMARY_READ}


def canonicalize_scopes(scopes: set[str]) -> set[str]:
    return {LEGACY_SCOPE_ALIASES.get(scope, scope) for scope in scopes}
