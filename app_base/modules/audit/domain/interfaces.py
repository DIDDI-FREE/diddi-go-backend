"""Ports owned by the audit module."""

from typing import Protocol

from app_base.modules.audit.domain.entities import BackofficeAuditEvent


class BackofficeAuditRepository(Protocol):
    async def record(self, event: BackofficeAuditEvent) -> BackofficeAuditEvent: ...
