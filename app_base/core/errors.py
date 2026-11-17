import logging
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app_base.core.observability import log_event

logger = logging.getLogger("uvicorn.error")

_WITHDRAWAL_PATHS = {
    "/v1/drivers/me/wallet/withdrawals",
    "/v1/drivers/me/wallet/withdrawals/quote",
    "/v1/drivers/me/wallet/withdrawals/verification/request",
}
_WITHDRAWAL_FIELDS = {
    "body", "query", "path", "header", "amount", "quote_id", "beneficiary_reference",
    "beneficiary_destination", "type", "phone", "network", "verification_id", "verification_code",
}
_SAFE_VALIDATION_TYPES = {
    "missing", "extra_forbidden", "uuid_parsing", "uuid_type", "uuid_version",
    "string_pattern_mismatch", "string_type", "string_too_short", "string_too_long",
    "int_parsing", "int_type", "int_from_float", "greater_than", "greater_than_equal",
    "literal_error", "model_attributes_type", "model_type", "json_invalid", "value_error",
}


@dataclass
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    details: Any | None = None


def api_error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
    *,
    request_id: str | None = None,
) -> JSONResponse:
    error = {"code": code, "message": message, "details": details}
    if request_id:
        error["request_id"] = request_id
    return JSONResponse(
        status_code=status_code,
        content={"error": error},
    )


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    request_id = getattr(_.state, "request_id", None)
    if _.url.path in _WITHDRAWAL_PATHS:
        log_event(
            "withdrawal.request.rejected", level="warning", request_id=request_id,
            path=_.url.path, method=_.method, status_code=exc.status_code, error_code=exc.code,
            user_id=getattr(getattr(_.state, "current_user", None), "id", None),
        )
    details = exc.details
    if request_id:
        if isinstance(details, dict):
            details = {**details, "request_id": request_id}
        elif details is None:
            details = {"request_id": request_id}
        else:
            details = {"request_id": request_id, "details": details}
    response = api_error_response(
        exc.status_code,
        exc.code,
        exc.message,
        details,
        request_id=request_id,
    )
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    if request.url.path in _WITHDRAWAL_PATHS:
        # Pydantic's input, ctx and even custom messages may contain OTPs or
        # phone numbers. Only allow known field names and built-in error types.
        violations = [{
            "loc": [part if part in _WITHDRAWAL_FIELDS else "<other>" for part in error.get("loc", ())],
            "type": error.get("type") if error.get("type") in _SAFE_VALIDATION_TYPES else "validation_error",
        } for error in exc.errors()[:20]]
        log_event(
            "withdrawal.request.validation_failed", level="warning", request_id=request_id,
            path=request.url.path, method=request.method, status_code=422,
            user_id=getattr(getattr(request.state, "current_user", None), "id", None),
            violations=violations, violation_count=len(exc.errors()),
        )
    details = {"violations": jsonable_encoder(exc.errors())}
    response = api_error_response(
        422,
        "VALIDATION_ERROR",
        "La requete ne respecte pas le contrat attendu.",
        details,
        request_id=request_id,
    )
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
    response = api_error_response(503, code, message, details, request_id=request_id)
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
        request_id=request_id,
    )
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response
