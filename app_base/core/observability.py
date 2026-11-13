"""DIDDI Observability v1 JSON logging with correlation and redaction."""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar, Token
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from app_base.core.metrics import record_business_event
from app_base.core.telemetry import current_trace_ids, resource_attributes

_request_id: ContextVar[str | None] = ContextVar("diddigo_request_id", default=None)
_LOGGER_NAME = "uvicorn.error"
_SENSITIVE = re.compile(
    r"(token|secret|password|passwd|cookie|authorization|api[_-]?key|signature|private[_-]?key|phone|email|ip_address|client_ip|signed_url)",
    re.I,
)
_MAX_BYTES = 64 * 1024


class DiddiJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, str):
            try:
                parsed = json.loads(record.msg)
                if isinstance(parsed, dict) and parsed.get("schema_version"):
                    return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
            except (TypeError, json.JSONDecodeError):
                pass
        return _encode(
            _payload(
                event="library.log",
                level=record.levelname.lower(),
                message=_safe_message(record.getMessage()),
                attributes={"logger": record.name},
            )
        )


def configure_observability(*, log_level: str = "INFO") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    for name in ("uvicorn.error", "diddigo"):
        logging.getLogger(name).setLevel(level)
    formatter = DiddiJsonFormatter()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        root.addHandler(handler)
    else:
        for handler in root.handlers:
            handler.setFormatter(formatter)


def bind_request_id(request_id: str | None) -> Token[str | None]:
    return _request_id.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)


def current_request_id() -> str | None:
    return _request_id.get()


def log_event(event: str, *, level: str = "info", message: str | None = None, **fields: Any) -> None:
    request_id = fields.pop("request_id", None) or current_request_id()
    trace_id, span_id = current_trace_ids()
    attributes = {key: _clean(key, value) for key, value in fields.items()}
    payload = _payload(
        event=event,
        level=level,
        message=message or event,
        attributes=attributes,
        request_id=request_id,
        trace_id=trace_id,
        span_id=span_id,
    )
    record_business_event(event, payload)
    logging.getLogger(_LOGGER_NAME).log(_levelno(level), _encode(payload))


def _payload(
    *,
    event: str,
    level: str,
    message: str,
    attributes: dict[str, Any],
    request_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "level": level.lower(),
        "event": event,
        "message": message,
        "resource": resource_attributes(),
        "attributes": attributes,
    }
    if request_id:
        payload["request_id"] = request_id
    if trace_id:
        payload["trace_id"] = trace_id
    if span_id:
        payload["span_id"] = span_id
    return payload


def _encode(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if len(encoded.encode()) <= _MAX_BYTES:
        return encoded
    attrs = payload.get("attributes", {})
    payload["attributes"] = {k: (str(v)[:2048] + "…" if isinstance(v, str) else v) for k, v in attrs.items()}
    payload["attributes"]["truncated"] = True
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))[: _MAX_BYTES - 1] + "}"


def _levelno(level: str) -> int:
    return getattr(logging, level.upper(), logging.INFO)


def _clean(key: str, value: Any) -> Any:
    return "[REDACTED]" if _SENSITIVE.search(key) else _json_safe(value)


def _safe_message(message: str) -> str:
    return re.sub(
        r"(?i)(authorization|bearer|token|secret|password|api[_-]?key)=?\s*[^\s,;]+",
        r"\1=[REDACTED]",
        message,
    )[:4096]


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
        return {str(k): _clean(str(k), v) for k, v in value.items()}
    if isinstance(value, list | tuple | set):
        return [_json_safe(v) for v in value]
    return str(value)
