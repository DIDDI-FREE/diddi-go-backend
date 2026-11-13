"""Bounded in-process Prometheus metrics for DIDDI Observability v1."""

from __future__ import annotations

import re
import threading
from collections import defaultdict
from collections.abc import Mapping
from typing import Any

_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
_STORE: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
_LOCK = threading.Lock()
_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
_HIST: dict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = defaultdict(lambda: [0.0] * (len(_BUCKETS) + 2))
_HIST_NAME = "diddi_http_server_request_duration_seconds"
_HELP = {
    "diddi_http_server_requests_total": "Total HTTP requests handled by DiddiGo.",
    _HIST_NAME: "HTTP server request duration in seconds.",
    "diddi_telemetry_dropped_total": "Telemetry signals dropped by DiddiGo.",
    "diddi_worker_heartbeat_timestamp_seconds": "Unix timestamp of the latest successful worker iteration.",
}
_GAUGES = {"diddi_worker_heartbeat_timestamp_seconds"}
_HISTOGRAMS = {_HIST_NAME}


def record_http_request(
    *, method: str, path: str, status_code: int, duration_ms: float, route: str | None = None
) -> None:
    method = (
        method.upper() if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"} else "OTHER"
    )
    route = route or normalize_path(path)
    labels = {"method": method, "route": route, "status_code": str(status_code)}
    increment("diddi_http_server_requests_total", labels)
    observe(_HIST_NAME, {"method": method, "route": route}, duration_ms / 1000)


def record_business_event(event: str, fields: Mapping[str, Any]) -> None:
    if event.startswith("http.request"):
        return
    fields = fields.get("attributes", fields)
    labels = {"event": event}
    for key in ("reason", "status", "status_code", "payment_method", "provider", "error_code", "ws_event", "role"):
        if fields.get(key) is not None:
            labels[key] = _clean_label_value(fields[key])
    increment("diddigo_business_events_total", labels)


def record_telemetry_drop(signal: str, reason: str) -> None:
    increment(
        "diddi_telemetry_dropped_total",
        {
            "signal": signal if signal in {"traces", "logs", "metrics"} else "other",
            "reason": reason if reason in {"export_error", "queue_full", "disabled", "invalid"} else "other",
        },
    )


def observe(name: str, labels: Mapping[str, Any], value: float) -> None:
    key = (name, _labels_tuple(labels))
    with _LOCK:
        buckets = _HIST[key]
        buckets[-2] += 1
        buckets[-1] += value
        for index, bound in enumerate(_BUCKETS):
            if value <= bound:
                buckets[index] += 1


def increment(name: str, labels: Mapping[str, Any] | None = None, amount: float = 1.0) -> None:
    with _LOCK:
        _STORE[(name, _labels_tuple(labels or {}))] += float(amount)


def set_value(name: str, value: float, labels: Mapping[str, Any] | None = None) -> None:
    with _LOCK:
        _STORE[(name, _labels_tuple(labels or {}))] = float(value)


def render_prometheus() -> str:
    lines: list[str] = []
    seen: set[str] = set()
    with _LOCK:
        store = sorted(_STORE.items())
        hist = sorted(_HIST.items())
    for (name, labels), value in store:
        if name not in seen:
            lines += [
                f"# HELP {name} {_HELP.get(name, name)}",
                f"# TYPE {name} {'gauge' if name in _GAUGES else 'counter'}",
            ]
            seen.add(name)
        lines.append(f"{name}{_format_labels(labels)} {_format_number(value)}")
    for (name, labels), buckets in hist:
        if name not in seen:
            lines += [f"# HELP {name} {_HELP[name]}", f"# TYPE {name} histogram"]
            seen.add(name)
        base = dict(labels)
        for index, bound in enumerate(_BUCKETS):
            bucket_labels = tuple(sorted({**base, "le": _format_number(bound)}.items()))
            lines.append(
                f"{name}_bucket{_format_labels(bucket_labels)} {_format_number(buckets[index])}"
            )
        lines.append(
            f"{name}_bucket{_format_labels(tuple(sorted({**base, 'le': '+Inf'}.items())))} "
            f"{_format_number(buckets[-2])}"
        )
        lines.append(f"{name}_count{_format_labels(labels)} {_format_number(buckets[-2])}")
        lines.append(f"{name}_sum{_format_labels(labels)} {_format_number(buckets[-1])}")
    return "\n".join(lines) + ("\n" if lines else "")


def reset_metrics() -> None:
    with _LOCK:
        _STORE.clear()
        _HIST.clear()


def normalize_path(path: str) -> str:
    return _UUID_RE.sub(":uuid", path) if path else "/_unmatched"


def _labels_tuple(labels: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((str(k), _clean_label_value(v)) for k, v in labels.items()))


def _clean_label_value(value: Any) -> str:
    value = str(value)
    return ":uuid" if _UUID_RE.fullmatch(value) else value[:120]


def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
    return "{" + ",".join(f'{k}="{_escape_label(v)}"' for k, v in labels) + "}" if labels else ""


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _format_number(value: float) -> str:
    numeric = float(value)
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:.6f}".rstrip("0").rstrip(".")
