"""Standard error envelope per spec §5.1. Duplicated from core-api."""

import uuid
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

log = get_logger(__name__)


def _envelope(code: str, message: str, request_id: str, status_code: int) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> ORJSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    code = _http_status_to_code(exc.status_code)
    return _envelope(code, str(exc.detail), request_id, exc.status_code)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> ORJSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return _envelope("VALIDATION_ERROR", "request failed validation", request_id, 422)


async def unhandled_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    log.exception("unhandled_exception", request_id=request_id)
    return _envelope("INTERNAL_ERROR", "internal server error", request_id, 500)


def _http_status_to_code(status_code: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }.get(status_code, "ERROR")


def install_handlers(app: Any) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
