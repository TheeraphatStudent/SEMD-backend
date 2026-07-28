"""Centralized exception handlers -- not yet registered against the live app.

`register_error_handlers(app)` is ready to call from `application.py`, but
doing so is the client-visible part of Phase 3 (ADR-0002) and needs its own
checkpoint per SEMD_BACKEND_REFACTOR_ROADMAP.md: converting the 61 existing
router `except Exception as e: raise HTTPException(500, detail=str(e))` call
sites happens feature-by-feature during Phase 4, not in one global sweep.

Response shape is additive: `detail` is preserved (so any client reading only
`response.json()["detail"]`, which is what FastAPI's default HTTPException
shape provides today, keeps working) alongside the new `type`/`title`/`code`/
`request_id`/`errors` fields from the mandate's proposed error contract.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.exceptions import AppError

logger = logging.getLogger('semd.errors')

_ERROR_TYPE_BASE = 'https://semd.internal/errors'


def _request_id(request: Request) -> str | None:
    return getattr(request.state, 'request_id', None)


def _error_response(
    request: Request,
    *,
    status: int,
    code: str,
    title: str,
    detail: str,
    errors: list | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            'type': f'{_ERROR_TYPE_BASE}/{code.lower().replace("_", "-")}',
            'title': title,
            'status': status,
            'code': code,
            'detail': detail,
            'instance': request.url.path,
            'request_id': _request_id(request),
            'errors': errors or [],
        },
    )


async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return _error_response(
        request,
        status=exc.status,
        code=exc.code,
        title=exc.code.replace('_', ' ').title(),
        detail=exc.detail,
        errors=exc.errors,
    )


async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(
        request,
        status=exc.status_code,
        code=f'HTTP_{exc.status_code}',
        title='HTTP Error',
        detail=str(exc.detail),
    )


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(
        request,
        status=422,
        code='VALIDATION_ERROR',
        title='Validation Error',
        detail='Request validation failed.',
        errors=list(exc.errors()),
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # This is the fix for the str(e)-leak finding in SEMD_BACKEND_CURRENT_STATE.md
    # section 5: the real exception is logged server-side (with request ID for
    # correlation), the client gets a generic message, never the raw exception text.
    logger.error(
        'unhandled exception',
        exc_info=exc,
        extra={'request_id': _request_id(request), 'path': request.url.path},
    )
    return _error_response(
        request,
        status=500,
        code='INTERNAL_ERROR',
        title='Internal Server Error',
        detail='An unexpected error occurred. Reference the request ID when reporting this.',
    )


def register_error_handlers(app: FastAPI) -> None:
    # Starlette's add_exception_handler stub is invariant on the handler's
    # exception-parameter type (wants exactly `Exception`), so a handler typed
    # to a specific subclass -- which is what lets these functions be precise
    # about what they receive -- always reads as a mismatch to mypy. This is
    # FastAPI's own documented registration pattern; narrowing away the
    # precise parameter types would cost more than the ignore does.
    app.add_exception_handler(AppError, handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, handle_unexpected_error)
