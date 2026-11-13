"""Request/response logging with correlation ids.

Container access logs are useful, but they do not tell us which authenticated
user hit which business route. This middleware emits one compact JSON line per
HTTP request so Portainer logs can be filtered by request_id, user_id, path, or
status code.
"""

from __future__ import annotations

import time
from urllib.parse import parse_qsl, urlencode
from uuid import uuid4

from opentelemetry import context, trace
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app_base.core.metrics import record_http_request
from app_base.core.observability import bind_request_id, log_event, reset_request_id
from app_base.core.telemetry import extract_context, valid_request_id

REQUEST_ID_STATE_KEY = "request_id"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = (
            valid_request_id(request.headers.get("x-request-id"))
            or valid_request_id(request.headers.get("x-correlation-id"))
            or str(uuid4())
        )
        setattr(request.state, REQUEST_ID_STATE_KEY, request_id)
        context_token = bind_request_id(request_id)
        started = time.perf_counter()
        status_code = 500
        token = context.attach(extract_context(dict(request.headers)))
        tracer = trace.get_tracer("diddigo.http")

        try:
            with tracer.start_as_current_span("HTTP " + request.method) as span:
                span.set_attribute("http.request.method", request.method)
                response = await call_next(request)
                span.set_attribute("http.response.status_code", response.status_code)
            if response.status_code is not None:
                status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            user = getattr(request.state, "current_user", None)
            route = getattr(request.scope.get("route"), "path", None) or "/_unmatched"
            record_http_request(
                method=request.method,
                path=request.url.path,
                route=route,
                status_code=status_code,
                duration_ms=duration_ms,
            )
            log_event(
                "http.request.completed",
                method=request.method,
                route=route,
                status_code=status_code,
                duration_ms=duration_ms,
                user_agent=request.headers.get("user-agent"),
                user_id=str(getattr(user, "id", "")) or None,
                user_role=getattr(user, "role", None),
            )
            reset_request_id(context_token)
            context.detach(token)


def get_request_id(request: Request) -> str | None:
    value = getattr(request.state, REQUEST_ID_STATE_KEY, None)
    return str(value) if value else None


def _safe_query(query: str) -> str:
    if not query:
        return ""
    hidden = {"token", "access_token", "refresh_token", "authorization"}
    pairs = [
        (key, "***" if key.lower() in hidden else value) for key, value in parse_qsl(query, keep_blank_values=True)
    ]
    return urlencode(pairs)
