"""Persistent privileged-operation audit records."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app_base.core.database import Base

_PG_UUID = PG_UUID(as_uuid=True)


class BackofficeAuditEventModel(Base):
    __tablename__ = "backoffice_events"
    __table_args__ = (
        UniqueConstraint(
            "client_id",
            "action",
            "idempotency_key",
            name="uq_audit_backoffice_command",
        ),
        Index("idx_audit_backoffice_target_created", "target_type", "target_id", "created_at"),
        Index("idx_audit_backoffice_actor_created", "actor_user_id", "created_at"),
        {"schema": "audit"},
    )

    id: Mapped[UUID] = mapped_column(_PG_UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    client_id: Mapped[str] = mapped_column(String(120), nullable=False)
    service_subject: Mapped[str] = mapped_column(String(160), nullable=False)
    actor_user_id: Mapped[UUID] = mapped_column(_PG_UUID, nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[UUID] = mapped_column(_PG_UUID, nullable=False)
    request_id: Mapped[UUID] = mapped_column(_PG_UUID, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()"),
    )
