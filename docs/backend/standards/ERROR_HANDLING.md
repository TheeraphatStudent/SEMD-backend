# Error Handling Standard

## Response shape

Every error response — from `core/error_handlers.py`, registered in `application.py` — has this shape, regardless of source:

```json
{
  "type": "https://semd.internal/errors/unsafe-url",
  "title": "Unsafe Url",
  "status": 422,
  "code": "UNSAFE_URL",
  "detail": "One or more URLs failed safety validation",
  "instance": "/prediction/predict",
  "request_id": "b6f2...",
  "errors": [{"url": "http://127.0.0.1/", "reason": "loopback address"}]
}
```

`detail` is preserved from the pre-existing `HTTPException(status_code, detail=...)` shape deliberately — this makes the rollout additive for any client that only reads `detail`, not a breaking change (see ADR-0002).

## Rules

1. **Domain/service code raises typed exceptions**, not `fastapi.HTTPException` directly, where the error represents a business rule (`core/exceptions.py::AppError` subclasses: `NotFoundError`, `ValidationError`, `PermissionDeniedError`, `UnauthorizedError`, `ConflictError`, `RateLimitError`, `ExternalServiceError`, `ServiceUnavailableError`, `NotImplementedFeatureError`). `HTTPException` remains fine for simple transport-level cases (e.g. a 404 with no special semantics) — both are caught and normalized to the same response shape.
2. **Routers do not catch generic `Exception`.** The 61-site `except Exception as e: raise HTTPException(500, detail=str(e))` pattern found throughout the pre-refactor codebase is gone from every domain audited (auth, users/roles, access keys, extension codes, prediction, third-party services, reports, flags, dashboard/stats, ML registry, training, queue) — confirmed removed, not just discouraged. A router may still catch a **specific** exception it needs to translate or clean up after (example: `routers/setting/access_key_route.py::create_extension_token` keeps `db.rollback()` in an `except Exception` block because it's the one method in that file that commits directly rather than delegating to a service).
3. **Internal errors never expose `str(e)`, stack traces, SQL text, tokens, or credentials to the client.** `core/error_handlers.py::handle_unexpected_error` logs the real exception server-side (`logger.error(..., exc_info=exc)`) with the request ID for correlation, and returns a fixed generic message. Verified with a test that plants a secret in an exception message and asserts it never reaches the response body (`tests/unit/test_core_error_handlers.py`).
4. **Every response carries a `request_id`** (from `core/middleware.py::RequestContextMiddleware`, echoed as the `X-Request-ID` response header too).
5. **Sensitive values are never logged** — see `docs/backend/standards/OBSERVABILITY.md`.

## Error-code registry

Codes actually in use, grepped from the codebase (not aspirational):

| Code | Status | Raised by | Meaning |
|---|---|---|---|
| `HTTP_<nnn>` (e.g. `HTTP_401`, `HTTP_403`) | matches status | `handle_http_exception` | Fallback for any plain `HTTPException` not yet migrated to a typed `AppError` — most of the codebase's existing business-rule 400/401/403/404 raises (see `services/auth_service.py`, `services/access_key_service.py`, etc.) still use `HTTPException` directly; they get this generic code rather than a specific one. Migrating these to typed codes is future work, not done wholesale (see auth-domain checkpoint's stated scope decision). |
| `VALIDATION_ERROR` | 422 | `handle_validation_error` (Pydantic request validation) and `core.exceptions.ValidationError` | Request body/query failed schema validation, or a domain-level validation rule failed |
| `UNSAFE_URL` | 422 | `core/security.py::reject_unsafe_urls` | A submitted URL failed the SSRF/scheme/credential/DNS-resolution safety check (Domain 5) |
| `NOT_FOUND` | 404 | `core.exceptions.NotFoundError` | (Available; specific domains mostly still use `HTTPException(404, ...)` directly) |
| `PERMISSION_DENIED` | 403 | `core.exceptions.PermissionDeniedError` | Object-level or role-based authorization failure — used for the URL-report ownership fix (Domain 2), the GLOBAL-flag admin gate (Domain 8) |
| `NOT_IMPLEMENTED` | 501 | `core.exceptions.NotImplementedFeatureError` | An endpoint is real and authenticated but its business logic doesn't exist yet — the 32 Dashboard/Stat stubs (Domain 9) and `GET /ml/service` (Domain 10) |
| `THIRD_PARTY_ERROR` | 502 | `services/client/third_service_executor.py` | A configured third-party detector returned an HTTP error status, or an unexpected error occurred calling it |
| `THIRD_PARTY_UNAVAILABLE` | 503 | `services/client/third_service_executor.py` | Connection to a third-party detector failed |
| `THIRD_PARTY_REDIRECT` | 502 | `services/client/third_service_executor.py` | A third-party detector returned a redirect (not followed, by design — see Domain 5/6) |
| `THIRD_PARTY_RESPONSE_TOO_LARGE` | 502 | `services/client/third_service_executor.py` | A third-party detector's response exceeded the 5 MiB size guard |
| `INTERNAL_ERROR` | 500 | `handle_unexpected_error` | Any exception not otherwise typed — real detail logged server-side only |

## What's deliberately not done

Converting every remaining `HTTPException(...)` raise across `services/auth_service.py`, `services/access_key_service.py`, etc. into a specific typed `AppError` subclass was explicitly scoped out during the auth-domain checkpoint (accepted by the user) — the safety goals (no leak, correct status code, no router-level mangling) are already met by removing the router-level catch-alls, since `handle_http_exception` normalizes any `HTTPException` to the same response shape regardless. Full migration remains available as low-risk future work, tracked per-domain, not bundled into this pass.
