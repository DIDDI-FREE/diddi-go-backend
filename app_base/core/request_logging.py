"""Request/response logging with correlation ids.

Container access logs are useful, but they do not tell us which authenticated
user hit which business route. This middleware emits one compact JSON line per
HTTP request so Portainer logs can be filtered by request_id, user_id, path, or
status code.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app_base.access")

REQUEST_ID_STATE_KEY = "request_id"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        setattr(request.state, REQUEST_ID_STATE_KEY, request_id)
        started = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            user = getattr(request.state, "current_user", None)
            now = datetime.now(UTC)
            log_payload = {
                "event": "http.request",
                "at": now.isoformat().replace("+00:00", "Z"),
                "hour": now.strftime("%Y-%m-%dT%H:00:00Z"),
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": _client_ip(request),
                "user_agent": request.headers.get("user-agent"),
                "user_id": str(getattr(user, "id", "")) or None,
                "user_role": getattr(user, "role", None),
            }
            logger.info(json.dumps(log_payload, ensure_ascii=False, separators=(",", ":")))


def get_request_id(request: Request) -> str | None:
    value = getattr(request.state, REQUEST_ID_STATE_KEY, None)
    return str(value) if value else None


def _client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return request.client.host if request.client else None
