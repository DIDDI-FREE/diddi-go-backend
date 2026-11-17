"""OpenTelemetry setup and bounded worker health for DIDDI Observability v1."""

from __future__ import annotations

import json
import logging
import re
import time
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

from app_base.core.metrics import record_telemetry_drop, set_value
from app_base.core.settings import settings

try:
    from opentelemetry import context, propagate, trace
    from opentelemetry._logs import SeverityNumber
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk._logs import LoggerProvider
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
except ImportError:  # pragma: no cover - dependency installation is deployment-owned
    context = propagate = trace = OTLPLogExporter = LoggerProvider = BatchLogRecordProcessor = SeverityNumber = None

_WORKERS: dict[str, float] = {}
_WORKER_ENABLED: dict[str, bool] = {}
_request_trace_id: ContextVar[str | None] = ContextVar("diddigo_trace_id", default=None)
_INSTANCE_ID = settings.service_instance_id or str(uuid4())
_LOGGER = logging.getLogger("diddigo.telemetry")
_log_provider = None
_trace_provider = None
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def valid_request_id(value: str | None) -> str | None:
    return value if value and _VALID_REQUEST_ID.fullmatch(value) else None


def resource_attributes() -> dict[str, str]:
    return {
        "service.namespace": "diddi",
        "service.name": "diddigo",
        "service.version": settings.service_version,
        "service.instance.id": _INSTANCE_ID,
        "deployment.environment.name": settings.environment,
        "diddi.deployment.id": settings.diddi_deployment_id,
        "diddi.component": settings.diddi_component,
        "diddi.observability.version": "1.1.3",
    }


def configure_telemetry() -> None:
    global _trace_provider
    if trace is None:
        return
    try:
        sampler = ParentBased(TraceIdRatioBased(settings.otel_traces_sampler_arg))
        headers = _parse_headers(settings.otel_exporter_otlp_headers)
        if settings.otel_exporter_otlp_endpoint:
            provider = TracerProvider(resource=Resource.create(resource_attributes()), sampler=sampler)
            endpoint = settings.otel_exporter_otlp_endpoint.rstrip("/")
            if not endpoint.endswith("/v1/traces"):
                endpoint += "/v1/traces"
            exporter = OTLPSpanExporter(
                endpoint=endpoint,
                headers=headers,
                timeout=settings.otel_export_timeout_seconds,
                certificate_file=_optional(settings.otel_exporter_otlp_ca_file),
                client_certificate_file=_optional(settings.otel_exporter_otlp_client_certificate_file),
                client_key_file=_optional(settings.otel_exporter_otlp_client_key_file),
            )
            provider.add_span_processor(
                BatchSpanProcessor(
                    exporter,
                    max_queue_size=settings.otel_max_queue_size,
                    schedule_delay_millis=settings.otel_schedule_delay_ms,
                    export_timeout_millis=int(settings.otel_export_timeout_seconds * 1000),
                )
            )
            _trace_provider = provider
            trace.set_tracer_provider(provider)
        _configure_log_exporter(headers)
    except Exception:
        # Collector configuration must never prevent the API from starting.
        return


def _configure_log_exporter(headers: dict[str, str]) -> None:
    global _log_provider
    if not settings.otel_logs_enabled or not settings.otel_exporter_otlp_logs_endpoint:
        return
    if LoggerProvider is None or BatchLogRecordProcessor is None or OTLPLogExporter is None:
        return
    try:
        _log_provider = LoggerProvider(resource=Resource.create(resource_attributes()))
        exporter = OTLPLogExporter(
            endpoint=settings.otel_exporter_otlp_logs_endpoint,
            headers=headers,
            timeout=settings.otel_export_timeout_seconds,
            certificate_file=_optional(settings.otel_exporter_otlp_ca_file),
            client_certificate_file=_optional(settings.otel_exporter_otlp_client_certificate_file),
            client_key_file=_optional(settings.otel_exporter_otlp_client_key_file),
        )
        _log_provider.add_log_record_processor(
            BatchLogRecordProcessor(
                exporter,
                max_queue_size=settings.otel_max_queue_size,
                schedule_delay_millis=settings.otel_schedule_delay_ms,
                export_timeout_millis=int(settings.otel_export_timeout_seconds * 1000),
            )
        )
        root = logging.getLogger()
        if not any(isinstance(handler, OTelLogHandler) for handler in root.handlers):
            root.addHandler(OTelLogHandler(_log_provider))
    except Exception:
        _log_provider = None


class OTelLogHandler(logging.Handler):
    """Non-blocking bridge from cleaned application JSON logs to OTLP logs."""

    def __init__(self, provider) -> None:
        super().__init__()
        self._logger = provider.get_logger("diddigo")

    def emit(self, record: logging.LogRecord) -> None:
        try:
            body = json.loads(record.msg) if isinstance(record.msg, str) else record.getMessage()
            if not isinstance(body, dict) or body.get("schema_version") != "1.0.0":
                body = {
                    "schema_version": "1.0.0",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "level": record.levelname.lower(),
                    "event": "library.log",
                    "message": _safe_message(record.getMessage()),
                    "resource": resource_attributes(),
                    "attributes": {"logger": record.name},
                }
            severity_name = "WARN" if record.levelname.upper() == "WARNING" else record.levelname.upper()
            severity = getattr(SeverityNumber, severity_name, SeverityNumber.INFO)
            self._logger.emit(body=body, severity_number=severity, severity_text=record.levelname.lower())
        except Exception:
            record_telemetry_drop("logs", "export_error")


def _safe_message(message: str) -> str:
    return re.sub(
        r"(?i)(authorization|bearer|token|secret|password|api[_-]?key)=?\s*[^\s,;]+", r"\1=[REDACTED]", message
    )[:4096]


def shutdown_telemetry() -> None:
    if _log_provider is not None:
        try:
            _log_provider.shutdown()
        except Exception:
            record_telemetry_drop("logs", "export_error")
    if _trace_provider is not None:
        try:
            _trace_provider.shutdown()
        except Exception:
            record_telemetry_drop("traces", "export_error")


def _parse_headers(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    return {item.split("=", 1)[0].strip(): item.split("=", 1)[1].strip() for item in value.split(",") if "=" in item}


def _optional(value: str | None) -> str | None:
    return value.strip() or None if value else None


def extract_context(headers: dict[str, str]):
    if propagate is None:
        return context.get_current()
    return propagate.extract(headers) or context.get_current()


def inject_context(headers: dict[str, str]) -> dict[str, str]:
    if propagate is not None:
        propagate.inject(headers)
    return headers


def current_trace_ids() -> tuple[str | None, str | None]:
    if trace is None:
        return _request_trace_id.get(), None
    span = trace.get_current_span()
    span_context = span.get_span_context()
    if not span_context.is_valid:
        return _request_trace_id.get(), None
    return format(span_context.trace_id, "032x"), format(span_context.span_id, "016x")


@contextmanager
def worker_iteration(worker_type: str):
    if trace is None:
        yield None
        heartbeat(worker_type)
        return
    tracer = trace.get_tracer("diddigo.worker")
    with tracer.start_as_current_span(f"worker.{worker_type}") as span:
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            raise
        else:
            heartbeat(worker_type)


def register_worker(worker_type: str, enabled: bool = True) -> None:
    _WORKER_ENABLED[worker_type] = enabled
    if enabled:
        set_value("diddi_worker_heartbeat_timestamp_seconds", 0, {"worker_type": worker_type})


def heartbeat(worker_type: str) -> None:
    now = time.time()
    _WORKERS[worker_type] = now
    set_value("diddi_worker_heartbeat_timestamp_seconds", now, {"worker_type": worker_type})


def worker_health(max_age_seconds: int = 120) -> dict[str, str]:
    now = time.time()
    return {
        name: ("ok" if not enabled or now - _WORKERS.get(name, 0) <= max_age_seconds else "stale")
        for name, enabled in _WORKER_ENABLED.items()
    }
