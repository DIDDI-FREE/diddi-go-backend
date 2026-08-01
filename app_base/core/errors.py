from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


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
    return api_error_response(exc.status_code, exc.code, exc.message, details)
