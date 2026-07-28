"""Typed application-exception hierarchy.

`control/`/`services/` code should raise these instead of `fastapi.HTTPException`,
so business logic stays free of the `fastapi` import (see ADR-0001, ADR-0002).
`core/error_handlers.py` converts these to the standardized response shape.

Not wired into any live route yet -- see SEMD_BACKEND_REFACTOR_ROADMAP.md
Phase 3 checkpoint. Building and unit-testing this now is inert; converting
the 61 existing router call sites to use it is the client-visible change that
needs a separate go-ahead.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for typed, expected application errors.

    status: the HTTP status code the error handler should respond with.
    code: a stable, machine-readable error code (see error-code registry,
        docs/backend/standards/ERROR_HANDLING.md once written).
    """

    status: int = 500
    code: str = 'INTERNAL_ERROR'

    def __init__(self, detail: str, *, code: str | None = None, errors: list | None = None):
        super().__init__(detail)
        self.detail = detail
        if code is not None:
            self.code = code
        self.errors = errors or []


class NotFoundError(AppError):
    status = 404
    code = 'NOT_FOUND'


class ValidationError(AppError):
    status = 422
    code = 'VALIDATION_ERROR'


class PermissionDeniedError(AppError):
    status = 403
    code = 'PERMISSION_DENIED'


class UnauthorizedError(AppError):
    status = 401
    code = 'UNAUTHORIZED'


class ConflictError(AppError):
    status = 409
    code = 'CONFLICT'


class RateLimitError(AppError):
    status = 429
    code = 'RATE_LIMITED'


class ExternalServiceError(AppError):
    """Upstream dependency (ML service, third-party detector, OAuth provider) failed."""
    status = 502
    code = 'EXTERNAL_SERVICE_ERROR'


class ServiceUnavailableError(AppError):
    """A required dependency (DB, Redis, ML queue) is unreachable or timed out."""
    status = 503
    code = 'SERVICE_UNAVAILABLE'


class NotImplementedFeatureError(AppError):
    """A registered, authenticated endpoint whose business logic hasn't been
    built yet -- distinct from ServiceUnavailableError (a working feature
    whose dependency is temporarily down). See Domain 9 (Dashboard/Stats):
    used for endpoints that are real, reachable, and honestly not implemented,
    rather than returning `None` and failing FastAPI's response validation.
    """
    status = 501
    code = 'NOT_IMPLEMENTED'
