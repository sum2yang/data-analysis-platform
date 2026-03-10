from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

__all__ = [
    "AppError",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "ExternalServiceError",
    "ErrorResponse",
    "register_error_handlers",
]

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str | None = None


class AppError(Exception):
    status_code: int = 500
    error: str = "internal_error"

    def __init__(self, detail: str | None = None, **kwargs: Any):
        self.detail = detail
        self.extra = kwargs
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = 404
    error = "not_found"


class ValidationError(AppError):
    status_code = 422
    error = "validation_error"


class AuthenticationError(AppError):
    status_code = 401
    error = "authentication_error"


class AuthorizationError(AppError):
    status_code = 403
    error = "authorization_error"


class ConflictError(AppError):
    status_code = 409
    error = "conflict"


class ExternalServiceError(AppError):
    status_code = 502
    error = "external_service_error"


def _build_response(status_code: int, error: str, detail: str | None) -> JSONResponse:
    body = ErrorResponse(error=error, detail=detail, code=error)
    return JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True))


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_req: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.exception("Server error: %s", exc.detail)
        return _build_response(exc.status_code, exc.error, exc.detail)

    @app.exception_handler(HTTPException)
    async def http_error_handler(_req: Request, exc: HTTPException) -> JSONResponse:
        return _build_response(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_req: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return _build_response(500, "internal_error", None)
