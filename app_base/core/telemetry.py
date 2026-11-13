"""OpenTelemetry setup and bounded worker health for DIDDI Observability v1."""

from __future__ import annotations

import re
import time
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4

from app_base.core.metrics import set_value
from app_base.core.settings import settings

try:
    from opentelemetry import context, propagate, trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
except ImportError:  # pragma: no cover - dependency installation is deployment-owned
    context = propagate = trace = None

_WORKERS: dict[str, float] = {}
_WORKER_ENABLED: dict[str, bool] = {}
_request_trace_id: ContextVar[str | None] = ContextVar("diddigo_trace_id", default=None)
_INSTANCE_ID = settings.service_instance_id or str(uuid4())
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
        "diddi.observability.version": "1.0.0",
    }


def configure_telemetry() -> None:
    if trace is None or not settings.otel_exporter_otlp_endpoint:
        return
    try:
        sampler = ParentBased(TraceIdRatioBased(settings.otel_traces_sampler_arg))
        provider = TracerProvider(resource=Resource.create(resource_attributes()), sampler=sampler)
        endpoint = settings.otel_exporter_otlp_endpoint.rstrip("/")
        if not endpoint.endswith("/v1/traces"):
            endpoint += "/v1/traces"
        headers = _parse_headers(settings.otel_exporter_otlp_headers)
        exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers, timeout=settings.otel_export_timeout_seconds)
        provider.add_span_processor(
            BatchSpanProcessor(
                exporter,
                max_queue_size=settings.otel_max_queue_size,
                schedule_delay_millis=settings.otel_schedule_delay_ms,
                export_timeout_millis=int(settings.otel_export_timeout_seconds * 1000),
            )
        )
        trace.set_tracer_provider(provider)
    except Exception:
        # Collector configuration must never prevent the API from starting.
        return


def _parse_headers(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    return {item.split("=", 1)[0].strip(): item.split("=", 1)[1].strip() for item in value.split(",") if "=" in item}


def extract_context(headers: dict[str, str]):
    return propagate.extract(headers) if propagate is not None else None


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
