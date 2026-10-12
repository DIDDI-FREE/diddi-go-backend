"""Shared operational eligibility rules for entering the matching pool."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app_base.core.error_codes import ErrorCode
from app_base.core.errors import ApiError
from app_base.core.observability import log_event
from app_base.modules.partner.application.services import PartnerService
from app_base.modules.payment.application.wallet_service import DriverWalletService


@dataclass
class DriverOnlineEligibilityService:
    wallets: DriverWalletService
    partners: PartnerService

    async def evaluate(self, driver_id: UUID) -> dict:
        blocked_by_partner, partner_reason = await self.partners.driver_is_blocked_by_partner(driver_id)
        wallet = await self.wallets.get_online_eligibility(driver_id)
        blocking_reasons: list[str] = []
        if blocked_by_partner:
            blocking_reasons.append("partner_suspended")
        if not wallet["eligible"]:
            blocking_reasons.append("driver_balance_too_low")
        return {
            "eligible": not blocking_reasons,
            "blocking_reasons": blocking_reasons,
            "partner": {"eligible": not blocked_by_partner, "reason": partner_reason},
            "wallet": wallet,
        }

    async def ensure_can_go_online(self, driver_id: UUID) -> None:
        result = await self.evaluate(driver_id)
        if not result["partner"]["eligible"]:
            log_event(
                "driver.online.blocked",
                level="warning",
                driver_id=driver_id,
                reason="partner_suspended",
                partner_reason=result["partner"]["reason"],
            )
            raise ApiError(
                403,
                ErrorCode.PARTNER_SUSPENDED,
                "Votre partenaire n'est pas actif. Vous ne pouvez pas passer en ligne.",
                {"reason": result["partner"]["reason"]},
            )
        if not result["wallet"]["eligible"]:
            wallet = result["wallet"]
            log_event(
                "driver.online.blocked",
                level="warning",
                driver_id=driver_id,
                reason="driver_balance_too_low",
                balance=wallet["balance"],
                min_balance=wallet["min_balance"],
                currency=wallet["currency"],
            )
            raise ApiError(
                403,
                ErrorCode.DRIVER_BALANCE_TOO_LOW,
                "Solde chauffeur insuffisant pour passer en ligne.",
                {
                    "balance": wallet["balance"],
                    "min_balance": wallet["min_balance"],
                    "currency": wallet["currency"],
                },
            )
