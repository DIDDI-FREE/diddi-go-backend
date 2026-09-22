import logging
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app_base.core.observability import log_event

logger = logging.getLogger("uvicorn.error")


@dataclass
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    details: Any | None = None


def api_error_response(status_code: int, code: str, message: str, details: Any | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    request_id = getattr(_.state, "request_id", None)
    details = exc.details
    if request_id:
        if isinstance(details, dict):
            details = {**details, "request_id": request_id}
        elif details is None:
            details = {"request_id": request_id}
        else:
            details = {"request_id": request_id, "details": details}
    response = api_error_response(exc.status_code, exc.code, exc.message, details)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


async def infrastructure_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    if isinstance(exc, SQLAlchemyError):
        code = "DATABASE_UNAVAILABLE"
        message = "Le service de base de donnees est temporairement indisponible."
    elif isinstance(exc, RedisError):
        code = "CACHE_UNAVAILABLE"
        message = "Le service temps reel est temporairement indisponible."
    else:  # pragma: no cover - registered only for the two classes above
        code = "DEPENDENCY_UNAVAILABLE"
        message = "Une dependance interne est temporairement indisponible."
    log_event(
        "dependency.unavailable",
        level="error",
        dependency_error=code,
        request_id=request_id,
        path=request.url.path,
        exception_type=type(exc).__name__,
    )
    details = {"request_id": request_id} if request_id else None
    response = api_error_response(503, code, message, details)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "unhandled_request_error request_id=%s path=%s exception_type=%s",
        request_id,
        request.url.path,
        type(exc).__name__,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    log_event(
        "http.unhandled_exception",
        level="error",
        request_id=request_id,
        path=request.url.path,
        exception_type=type(exc).__name__,
    )
    details = {"request_id": request_id} if request_id else None
    response = api_error_response(
        500,
        "INTERNAL_SERVER_ERROR",
        "Une erreur interne inattendue est survenue.",
        details,
    )
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response
