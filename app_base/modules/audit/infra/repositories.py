"""SQLAlchemy adapter for the privileged-operation audit trail."""

from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app_base.modules.audit.domain.entities import BackofficeAuditEvent
from app_base.modules.audit.domain.interfaces import BackofficeAuditRepository
from app_base.modules.audit.infra.models import BackofficeAuditEventModel


class SqlAlchemyBackofficeAuditRepository(BackofficeAuditRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, event: BackofficeAuditEvent) -> BackofficeAuditEvent:
        values = {
            "id": event.id,
            "client_id": event.client_id,
            "service_subject": event.service_subject,
            "actor_user_id": event.actor_user_id,
            "action": event.action,
            "target_type": event.target_type,
            "target_id": event.target_id,
            "request_id": event.request_id,
            "idempotency_key": event.idempotency_key,
            "outcome": event.outcome,
            "reason": event.reason,
            "context": event.context,
            "created_at": event.created_at,
        }
        statement = (
            insert(BackofficeAuditEventModel)
            .values(**values)
            .on_conflict_do_nothing(constraint="uq_audit_backoffice_command")
            .returning(BackofficeAuditEventModel.id)
        )
        inserted_id = (await self._session.execute(statement)).scalar_one_or_none()
        if inserted_id is not None:
            return event

        existing = (
            await self._session.execute(
                select(BackofficeAuditEventModel).where(
                    BackofficeAuditEventModel.client_id == event.client_id,
                    BackofficeAuditEventModel.action == event.action,
                    BackofficeAuditEventModel.idempotency_key == event.idempotency_key,
                ),
            )
        ).scalar_one()
        return replace(event, id=existing.id, created_at=existing.created_at)
