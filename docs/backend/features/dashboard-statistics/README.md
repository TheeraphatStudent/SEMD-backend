# Feature: Dashboard and Statistics (Domain 9)

## Not a refactor — 32 endpoints were non-functional stubs

Confirmed independently for all 7 router files (`routers/dashboard/dashboard_route.py` + 6 `routers/stat/*.py`) during Phase 1 and re-verified here: every handler body was a bare `pass` (implicitly `return None`), with a declared Pydantic `response_model` on every route and **zero `AuthGuard` dependency anywhere in any of the 32 endpoints**. Consequence, verified: FastAPI's response validation rejects `None` against a non-optional response model, so **every one of these 32 endpoints has always returned an unhandled 500 to any caller, ever** — they were never reachable in a working state, and were also fully unauthenticated the whole time.

## What was fixed (scoped-safe, per the explicit instruction not to invent metric semantics)

1. **Authentication added** — every one of the 32 handlers now takes `current_user: User = Depends(AuthGuard.get_current_user)`, matching every other domain in this backend. Unauthenticated calls now get `401`, not a silent pass-through to broken logic.
2. **Honest `501` instead of a response-validation crash** — every handler now `raise NotImplementedFeatureError(...)` (new `core.exceptions.NotImplementedFeatureError`, status 501, code `NOT_IMPLEMENTED`). This is not new information to API consumers — every one of these routers already declared `501: {"description": "Not implemented"}` in its own `responses={}` dict from the start, so the router authors already knew and documented that these weren't built; the code just never actually returned that status. Now it does.

## What was deliberately not built

Real statistics computation. Doing so requires: which time window (last 24h? 30d? all-time?), what "system performance" even measures in this codebase (there's no APM/metrics collection anywhere — `GET /health` returns hardcoded fake CPU/memory/disk figures, so there's no real system-metrics source to aggregate from), whether these are member-scoped or admin-only per endpoint, what "trend" buckets look like (daily? hourly?), and what queries back each of the 32 distinct response shapes (`SystemStatResponse`, `UserActivityResponse`, `PredictionByModelResponse`, etc. — 24 distinct Pydantic models across the 6 stat routers alone). None of this is specified anywhere in the codebase, its docs, or the OpenAPI schema beyond field names and types. Building it would mean inventing business semantics wholesale — explicitly prohibited by the mandate ("create fake requirements not found in code or documentation"). This is the concrete instance of that prohibition, not a hypothetical one.

**Recommendation for whoever picks this up next**: before writing any aggregation query, get the product owner to specify, per endpoint, the time window, the grouping/bucketing, and the audience (member vs admin) — the response model field names alone (e.g. `TopUserResponse`, `ApiEndpointStatResponse`) hint at intent but don't fully specify it.

## Client-visible change

All 32 endpoints: `500` (unconditional crash) → `401` (no token) or `501` (authenticated, not implemented). This is a status-code correction from a state where the endpoint could never have succeeded for any caller — not a behavior regression for any working integration, since none could have existed.

## Testing

`tests/unit/test_dashboard_stub_endpoints.py` (new): spot-checks one endpoint per router (8 total, mechanically representative of all 32) — confirms `401` without auth, `501` with auth, and that the 501 body carries `code: NOT_IMPLEMENTED`.

## Migration / rollback

`git checkout -- routers/dashboard/dashboard_route.py routers/stat/ core/exceptions.py tests/unit/test_dashboard_stub_endpoints.py`. No DB/schema impact — these endpoints never touched the database (there was no logic to touch it with).
