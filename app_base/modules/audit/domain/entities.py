"""Audit domain entities without infrastructure dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class BackofficeAuditEvent:
    client_id: str
    service_subject: str
    actor_user_id: UUID
    action: str
    target_type: str
    target_id: UUID
    request_id: UUID
    idempotency_key: str
    outcome: str = "completed"
    reason: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
