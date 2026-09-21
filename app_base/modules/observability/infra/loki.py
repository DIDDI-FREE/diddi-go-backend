from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any

import httpx

from app_base.core.errors import ApiError
from app_base.modules.observability.domain.interfaces import OperationalLogRepository


class LokiOperationalLogRepository(OperationalLogRepository):
    def __init__(self) -> None:
        self._base_url = os.getenv("LOKI_BASE_URL", "http://loki:3100").rstrip("/")
        self._service_label = os.getenv("LOKI_DIDDIGO_SERVICE_LABEL", "app")
        self._timeout_seconds = float(os.getenv("LOKI_TIMEOUT_SECONDS", "5"))

    async def search(
        self,
        *,
        field: str,
        value: str,
        start: datetime,
        end: datetime,
        level: str | None,
        limit: int,
        cursor: str | None,
    ) -> dict:
        end_ns = _cursor_or_timestamp(cursor, end)
        query = _build_query(self._service_label, field, value, level)
        params = {
            "query": query,
            "start": str(_to_ns(start)),
            "end": str(end_ns),
            "direction": "backward",
            "limit": str(limit + 1),
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(f"{self._base_url}/loki/api/v1/query_range", params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ApiError(
                503,
                "LOG_SEARCH_UNAVAILABLE",
                "Le service de recherche des logs est indisponible.",
            ) from exc

        entries = _parse_loki_result(payload)
        has_more = len(entries) > limit
        visible = entries[:limit]
        next_cursor = str(int(visible[-1]["timestamp_ns"]) - 1) if has_more and visible else None
        for entry in visible:
            entry.pop("timestamp_ns", None)
        return {
            "items": visible,
            "next_cursor": next_cursor,
            "limit": limit,
            "from": start.isoformat(),
            "to": end.isoformat(),
        }


def _build_query(service_label: str, field: str, value: str, level: str | None) -> str:
    selector = f'{{compose_service={json.dumps(service_label)}}}'
    filters = ["| json", f"| {field}={json.dumps(value)}"]
    if level:
        filters.append(f"| level={json.dumps(level)}")
    return " ".join([selector, *filters])


def _parse_loki_result(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("status") != "success":
        raise ApiError(503, "LOG_SEARCH_UNAVAILABLE", "Loki a retourne une reponse invalide.")

    entries: list[dict[str, Any]] = []
    for stream in payload.get("data", {}).get("result", []):
        labels = stream.get("stream", {})
        for timestamp_ns, raw_line in stream.get("values", []):
            try:
                event = json.loads(raw_line)
            except (TypeError, json.JSONDecodeError):
                event = {"message": str(raw_line)}
            timestamp = datetime.fromtimestamp(int(timestamp_ns) / 1_000_000_000, tz=UTC).isoformat()
            known = {"at", "level", "event", "message", "request_id"}
            entries.append(
                {
                    "timestamp": event.get("at", timestamp),
                    "timestamp_ns": str(timestamp_ns),
                    "level": event.get("level", labels.get("level", "INFO")),
                    "event": event.get("event", "container.log"),
                    "message": event.get("message"),
                    "request_id": event.get("request_id"),
                    "metadata": {key: value for key, value in event.items() if key not in known},
                }
            )
    entries.sort(key=lambda item: int(item["timestamp_ns"]), reverse=True)
    return entries


def _cursor_or_timestamp(cursor: str | None, fallback: datetime) -> int:
    if cursor is None:
        return _to_ns(fallback)
    try:
        value = int(cursor)
    except ValueError as exc:
        raise ApiError(422, "INVALID_LOG_CURSOR", "Le curseur de logs est invalide.") from exc
    if value < 0:
        raise ApiError(422, "INVALID_LOG_CURSOR", "Le curseur de logs est invalide.")
    return value


def _to_ns(value: datetime) -> int:
    return int(value.timestamp() * 1_000_000_000)
