"""Payment module — PostgreSQL tables in the `payment` schema.

Mirrors architecture doc §3.3 exactly:
    payment.transactions(id, ride_id, amount, currency, method, status,
                         collected_by, collected_at, created_at)

Cash-only at launch. Column types per spec: amount NUMERIC(10,2),
currency CHAR(3) default 'XOF', method 'cash'. The `ride_id` is a logical
reference (no ForeignKey here — cross-schema FKs are fine at the DB level,
but `ride` and `payment` are meant to be extractable into separate services,
so the contract is enforced at the application layer).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app_base.core.database import Base

_PG_UUID = PG_UUID(as_uuid=True)


class TransactionModel(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_payment_ride", "ride_id"),
        {"schema": "payment"},
    )

    id: Mapped[UUID] = mapped_column(
        _PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"),
    )
    ride_id: Mapped[UUID] = mapped_column(_PG_UUID, nullable=False)  # logical ref to ride.rides(id)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="XOF")
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="cash")  # cash → mobile_money/wallet later
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending | collected | disputed
    collected_by: Mapped[UUID | None] = mapped_column(
        _PG_UUID, nullable=True,
    )  # driver_profiles.id, confirmed collector
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )
