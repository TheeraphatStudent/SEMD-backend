# ADR 0002: Typed `AppError` hierarchy + centralized handlers, RFC-7807-flavored response

## Status
Accepted

## Context
The current-state audit found `except Exception as e: raise HTTPException(status_code=500, detail=str(e))` duplicated across 61 router call sites, with zero global exception handlers registered anywhere (`SEMD_BACKEND_CURRENT_STATE.md` §5). This leaks raw Python exception text (`str(e)`) to clients — a real information-disclosure issue, not just a style problem — and gives no error-code registry for programmatic clients (web frontend, browser extension) to branch on.

## Decision
1. Introduce `core/exceptions.py`: a small `AppError` base and subclasses (`NotFoundError`, `ValidationError`, `PermissionError`, `ConflictError`, `ExternalServiceError`, `RateLimitError`, ...) that `control/`/`services/` raise instead of `fastapi.HTTPException`.
2. Introduce `core/error_handlers.py`: `@app.exception_handler(AppError)` plus a catch-all `@app.exception_handler(Exception)` that logs the real exception server-side (with request ID) and returns a generic, non-leaking message to the client for anything unexpected.
3. Response shape follows the mandate's proposed structure: `type`, `title`, `status`, `code`, `detail`, `instance`, `request_id`, `errors`.
4. Routers stop wrapping calls in `try/except Exception`; they let typed errors propagate to the handlers. A router may still catch a specific exception it needs to translate to a different HTTP status than its default mapping.

## Alternatives rejected
- **Keep per-router try/except but stop leaking `str(e)`.** Rejected: fixes the leak but not the 61x duplication, and still requires every new endpoint to remember to add the pattern correctly.
- **Use FastAPI's built-in `HTTPException` everywhere with richer `detail` dicts, no new exception hierarchy.** Rejected: `HTTPException` conflates "this is a transport-level HTTP error" with "this is a business rule violation," which is exactly the coupling ADR-0001 flags as the one real dependency-direction issue in the current codebase. A typed hierarchy lets `control/`/`services/` stay free of `fastapi` imports.

## Consequences
- One-time cost: every one of the 61 existing call sites needs to be touched during Phase 3/4 to remove the local try/except (mechanical, low-risk, but non-trivial diff size — sequence per-feature per the roadmap, not all at once).
- Error-code registry (`docs/backend/standards/ERROR_HANDLING.md`) becomes a real contract clients can depend on, versus today's ad hoc `detail` strings.
- Unexpected errors are logged server-side for the first time (currently: nothing is logged on the generic-exception path at all).
