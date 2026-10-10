"""SQL aggregates for the Pilotage daily ride summary."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, case, exists, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.payment.infra.models import (
    DriverTopupModel,
    DriverWithdrawalModel,
    TransactionModel,
)
from app_base.modules.ride.domain.summary import RideFinanceSummaryTotals, RideSummaryTotals
from app_base.modules.ride.infra.models import RideModel


class SqlAlchemyRideSummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def summarize_period(self, start: datetime, end: datetime) -> RideSummaryTotals:
        requested = (
            select(func.count(RideModel.id))
            .where(RideModel.requested_at >= start, RideModel.requested_at < end)
            .scalar_subquery()
        )
        completed = (
            select(
                func.count(RideModel.id).label("rides_completed"),
                func.coalesce(
                    func.sum(case((RideModel.currency == "XOF", RideModel.final_fare))),
                    0,
                ).label("completed_fare_total_xof"),
                func.count(RideModel.id)
                .filter(RideModel.currency == "XOF", RideModel.final_fare.is_(None))
                .label("completed_rides_without_fare"),
            )
            .where(
                RideModel.status == "completed",
                RideModel.completed_at >= start,
                RideModel.completed_at < end,
            )
            .subquery()
        )
        row = (
            await self._session.execute(
                select(
                    requested.label("rides_requested"),
                    completed.c.rides_completed,
                    completed.c.completed_fare_total_xof,
                    completed.c.completed_rides_without_fare,
                )
            )
        ).one()
        return RideSummaryTotals(
            rides_requested=int(row.rides_requested),
            rides_completed=int(row.rides_completed),
            completed_fare_total_xof=Decimal(row.completed_fare_total_xof),
            completed_rides_without_fare=int(row.completed_rides_without_fare),
        )

    async def summarize_finance_period(self, start: datetime, end: datetime) -> RideFinanceSummaryTotals:
        completed_filter = (
            RideModel.status == "completed",
            RideModel.completed_at >= start,
            RideModel.completed_at < end,
            RideModel.currency == "XOF",
        )
        collected_cash = exists(
            select(TransactionModel.id).where(
                TransactionModel.ride_id == RideModel.id,
                TransactionModel.currency == "XOF",
                TransactionModel.status == "collected",
            )
        )
        succeeded_digital = exists(
            select(TransactionModel.id).where(
                TransactionModel.ride_id == RideModel.id,
                TransactionModel.currency == "XOF",
                TransactionModel.status == "succeeded",
            )
        )
        fully_refunded = exists(
            select(TransactionModel.id).where(
                TransactionModel.ride_id == RideModel.id,
                TransactionModel.currency == "XOF",
                TransactionModel.status == "refunded",
            )
        )
        rides = (
            select(
                func.coalesce(func.sum(RideModel.final_fare), 0).label("completed_fare_total_xof"),
                func.coalesce(
                    func.sum(
                        case(
                            (RideModel.payment_method.in_(("diddipay", "wave")), RideModel.final_fare),
                            else_=0,
                        )
                    ),
                    0,
                ).label("digital_payments_xof"),
                func.coalesce(
                    func.sum(case((RideModel.payment_method == "cash", RideModel.final_fare), else_=0)),
                    0,
                ).label("cash_payments_xof"),
                func.coalesce(func.sum(RideModel.platform_commission), 0).label("platform_commission_xof"),
                func.coalesce(func.sum(RideModel.driver_payout_estimate), 0).label("driver_earnings_xof"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                or_(
                                    and_(RideModel.payment_method == "cash", collected_cash),
                                    and_(RideModel.payment_method.in_(("diddipay", "wave")), succeeded_digital),
                                ),
                                RideModel.driver_payout_estimate,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("driver_amount_paid_xof"),
                func.coalesce(
                    func.sum(case((fully_refunded, RideModel.final_fare), else_=0)),
                    0,
                ).label("refunds_xof"),
            )
            .where(*completed_filter)
            .subquery()
        )
        topups_requested = (
            select(
                func.count(DriverTopupModel.id).label("driver_topups_requested_count"),
                func.coalesce(func.sum(DriverTopupModel.amount), 0).label("driver_topups_requested_xof"),
            )
            .where(
                DriverTopupModel.created_at >= start,
                DriverTopupModel.created_at < end,
                DriverTopupModel.currency == "XOF",
            )
            .subquery()
        )
        topups_succeeded = (
            select(
                func.count(DriverTopupModel.id)
                .filter(DriverTopupModel.status == "succeeded")
                .label("driver_topups_succeeded_count"),
                func.coalesce(
                    func.sum(DriverTopupModel.amount).filter(DriverTopupModel.status == "succeeded"),
                    0,
                ).label("driver_topups_succeeded_xof"),
            )
            .where(
                DriverTopupModel.paid_at >= start,
                DriverTopupModel.paid_at < end,
                DriverTopupModel.currency == "XOF",
            )
            .subquery()
        )
        topups_state = (
            select(
                func.count(DriverTopupModel.id)
                .filter(DriverTopupModel.status.in_(("pending", "requires_action", "processing")))
                .label("driver_topups_pending_count"),
                func.coalesce(
                    func.sum(DriverTopupModel.amount).filter(
                        DriverTopupModel.status.in_(("pending", "requires_action", "processing"))
                    ),
                    0,
                ).label("driver_topups_pending_xof"),
                func.count(DriverTopupModel.id)
                .filter(DriverTopupModel.status.in_(("failed", "cancelled")))
                .label("driver_topups_failed_count"),
                func.coalesce(
                    func.sum(DriverTopupModel.amount).filter(DriverTopupModel.status.in_(("failed", "cancelled"))),
                    0,
                ).label("driver_topups_failed_xof"),
            )
            .where(
                DriverTopupModel.created_at >= start,
                DriverTopupModel.created_at < end,
                DriverTopupModel.currency == "XOF",
            )
            .subquery()
        )
        withdrawals = (
            select(
                func.count(DriverWithdrawalModel.id).label("driver_withdrawals_requested_count"),
                func.coalesce(func.sum(DriverWithdrawalModel.amount), 0).label("driver_withdrawals_requested_xof"),
                func.count(DriverWithdrawalModel.id)
                .filter(DriverWithdrawalModel.status.in_(("reserved", "processing")))
                .label("driver_withdrawals_processing_count"),
                func.coalesce(
                    func.sum(DriverWithdrawalModel.amount).filter(
                        DriverWithdrawalModel.status.in_(("reserved", "processing"))
                    ),
                    0,
                ).label("driver_withdrawals_processing_xof"),
                func.count(DriverWithdrawalModel.id)
                .filter(DriverWithdrawalModel.status == "succeeded")
                .label("driver_withdrawals_succeeded_count"),
                func.coalesce(
                    func.sum(DriverWithdrawalModel.amount).filter(DriverWithdrawalModel.status == "succeeded"),
                    0,
                ).label("driver_withdrawals_succeeded_xof"),
                func.count(DriverWithdrawalModel.id)
                .filter(DriverWithdrawalModel.status == "released")
                .label("driver_withdrawals_released_count"),
                func.coalesce(
                    func.sum(DriverWithdrawalModel.amount).filter(DriverWithdrawalModel.status == "released"),
                    0,
                ).label("driver_withdrawals_released_xof"),
                func.coalesce(
                    func.sum(DriverWithdrawalModel.fees).filter(DriverWithdrawalModel.status == "succeeded"),
                    0,
                ).label("withdrawal_fees_xof"),
            )
            .where(
                DriverWithdrawalModel.created_at >= start,
                DriverWithdrawalModel.created_at < end,
                DriverWithdrawalModel.currency == "XOF",
            )
            .subquery()
        )
        sources = (
            rides.join(topups_requested, true())
            .join(topups_succeeded, true())
            .join(topups_state, true())
            .join(withdrawals, true())
        )
        row = (
            await self._session.execute(
                select(rides, topups_requested, topups_succeeded, topups_state, withdrawals).select_from(sources)
            )
        ).one()
        return RideFinanceSummaryTotals(
            completed_fare_total_xof=Decimal(row.completed_fare_total_xof),
            digital_payments_xof=Decimal(row.digital_payments_xof),
            cash_payments_xof=Decimal(row.cash_payments_xof),
            platform_commission_xof=Decimal(row.platform_commission_xof),
            driver_earnings_xof=Decimal(row.driver_earnings_xof),
            driver_amount_paid_xof=Decimal(row.driver_amount_paid_xof),
            refunds_xof=Decimal(row.refunds_xof),
            driver_topups_requested_count=int(row.driver_topups_requested_count),
            driver_topups_requested_xof=Decimal(row.driver_topups_requested_xof),
            driver_topups_succeeded_count=int(row.driver_topups_succeeded_count),
            driver_topups_succeeded_xof=Decimal(row.driver_topups_succeeded_xof),
            driver_topups_pending_count=int(row.driver_topups_pending_count),
            driver_topups_pending_xof=Decimal(row.driver_topups_pending_xof),
            driver_topups_failed_count=int(row.driver_topups_failed_count),
            driver_topups_failed_xof=Decimal(row.driver_topups_failed_xof),
            driver_withdrawals_requested_count=int(row.driver_withdrawals_requested_count),
            driver_withdrawals_requested_xof=Decimal(row.driver_withdrawals_requested_xof),
            driver_withdrawals_processing_count=int(row.driver_withdrawals_processing_count),
            driver_withdrawals_processing_xof=Decimal(row.driver_withdrawals_processing_xof),
            driver_withdrawals_succeeded_count=int(row.driver_withdrawals_succeeded_count),
            driver_withdrawals_succeeded_xof=Decimal(row.driver_withdrawals_succeeded_xof),
            driver_withdrawals_released_count=int(row.driver_withdrawals_released_count),
            driver_withdrawals_released_xof=Decimal(row.driver_withdrawals_released_xof),
            withdrawal_fees_xof=Decimal(row.withdrawal_fees_xof),
        )
