"""Small observability helpers for logs that stay readable in Portainer.

Sprint 0.5 deliberately keeps this lightweight: one JSON event per important
operation, with request correlation through a context variable. Metrics,
persistent event tables and dashboards can build on top later.
"""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

_request_id: ContextVar[str | None] = ContextVar("diddigo_request_id", default=None)
_LOGGER_NAME = "uvicorn.error"


def configure_observability(*, log_level: str = "INFO") -> None:
    """Make app logs visible and level-controlled in Docker/Portainer."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(level)
    logging.getLogger(_LOGGER_NAME).setLevel(level)
    logging.getLogger("diddigo").setLevel(level)


def bind_request_id(request_id: str | None) -> Token[str | None]:
    return _request_id.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)


def current_request_id() -> str | None:
    return _request_id.get()


def log_event(event: str, *, level: str = "info", message: str | None = None, **fields: Any) -> None:
    """Emit a compact JSON business event.

    We log through `uvicorn.error` because that logger is already connected to
    the container console in the current deployment.
    """
    logger = logging.getLogger(_LOGGER_NAME)
    now = datetime.now(UTC)
    payload = {
        "event": event,
        "at": now.isoformat().replace("+00:00", "Z"),
        "level": level.upper(),
        "request_id": fields.pop("request_id", None) or current_request_id(),
    }
    if message:
        payload["message"] = message
    payload.update({key: _json_safe(value) for key, value in fields.items()})
    logger.log(_levelno(level), json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def _levelno(level: str) -> int:
    return getattr(logging, level.upper(), logging.INFO)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=UTC)
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_json_safe(item) for item in value]
    return str(value)
