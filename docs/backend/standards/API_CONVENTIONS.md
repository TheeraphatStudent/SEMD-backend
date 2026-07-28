# API Conventions

Documents actual, implemented conventions — not aspirational ones. Where the codebase is inconsistent, that's stated explicitly rather than papered over.

## Base path and versioning

`FastAPI(root_path='/api', ...)` (`application.py`) — every route is served under `/api` at the reverse-proxy/client level, but router prefixes themselves (`/auth`, `/ml`, `/setting/...`, `/prediction`, `/report`, `/stat/...`, `/dashboard`, `/queue`, `/health`) don't repeat `/api`. **No version segment** (`/v1`, etc.) anywhere except the orphaned `MLTrainingRouter`, which used `/api/v1/ml/training` before Domain 10 normalized it to `/ml/training` to match everything else. There is no API-versioning strategy in this codebase today — a breaking change would need a new prefix or a parallel router, decided when it's actually needed.

## Resource naming

Mostly REST-ish but not strict: `/setting/access-key/{key_id}/usage/monthly` mixes resource nesting with an action-like suffix; `/ml/models/{model_id}/promote` and `/activate`/`/deactivate` are verb-suffixed action endpoints rather than pure resource PATCH/PUT. Kebab-case for multi-word path segments (`access-key`, `third-service`, `url-flag`). Admin-scoped sibling resources use an `/admin` path segment rather than a query param or header (`/setting/access-key/admin`, `/auth/users`) — inconsistent between domains (access keys use `/admin` prefix, users use a separate `UserRoute` at `/auth/users` entirely). Not unified in this pass — flagged as a cosmetic inconsistency, not a bug.

## HTTP methods and status codes

Standard verb usage (GET read, POST create/action, PUT update, PATCH partial update — used only for `/ml/models/{id}/stage`, DELETE remove). Status codes: `200` default success, `201` for creation (inconsistently — some create endpoints declare `201` at the route level, others return `200` in the body's `status` field while the actual HTTP status stays `200`; see `routers/setting/access_key_route.py::create_extension_token`, which fixed this pass returns HTTP `200` with body `status: 201` — a pre-existing mismatch between the body field and the real header, not corrected repo-wide since it's cosmetic and every client already has to read the real HTTP status regardless). `204` for `DELETE /ml/models/{id}`. `501` for genuinely unimplemented endpoints (Domain 9/10 fix — see `ERROR_HANDLING.md`'s `NOT_IMPLEMENTED` code).

## Pagination

`libs/pagination.py::PaginationParams`/`PaginationMeta`/`create_pagination_meta` — used by `GET /auth/users`, `GET /setting/access-key/*`. Query params: `page`, `page_size` (or `skip`/`limit` directly in a few older endpoints like `GET /report`, `GET /setting/url-flag` — **inconsistent**, not unified). No cursor-based pagination anywhere.

## Filtering / sorting / search

Ad hoc per-endpoint query params (`service_type`, `algorithm`, `stage`) — no generic filter/sort query-param convention (no `?sort=`, `?filter[x]=`). Not built beyond what each endpoint already needed.

## Date formats

ISO 8601 throughout (`datetime.isoformat()` / Pydantic's default). **Not UTC-aware consistently** — most code uses `datetime.utcnow()` (naive datetime, no `tzinfo`), which is deprecated since Python 3.12 (confirmed via multiple `DeprecationWarning`s during test runs, e.g. `services/url_report_service.py`, `routers/setting/access_key_route.py`). Not fixed repo-wide in this pass (mechanical but wide-reaching — every `datetime.utcnow()` call site — flagged as cleanup, not a correctness bug today since the app doesn't currently compare naive and aware datetimes).

## Enum serialization

Pydantic string enums (`class RoleType(str, Enum)`, etc. in `libs/types/enums.py`) serialize as their string value in JSON — consistent throughout.

## Empty / no-content responses

`DELETE /ml/models/{id}` returns `204` with no body (the only true no-content response). Every other delete/action endpoint returns a `BaseResponseModel` body (`status`, `message`) even on success — inconsistent with the 204 case, not unified.

## Error responses

See `ERROR_HANDLING.md` — one shape for every error, everywhere, as of the Domain 2-13 sweep.

## Idempotency

**No idempotency-key support anywhere.** POST endpoints that create resources (access keys, url flags, url reports, ML models) have no dedupe mechanism — a retried request creates a duplicate. Not built; flagged as a gap, not fixed.

## Deprecation

No deprecation mechanism exists (no `Deprecated` response header, no OpenAPI `deprecated: true` flags in use). Not needed yet — nothing in this backend has been deprecated.

## Request IDs

`X-Request-ID` request header is honored if the client sends one (passthrough), otherwise generated server-side (`core/middleware.py::RequestContextMiddleware`). Always present in the response header and in every structured log line and error body for that request.

## Authentication

Two independent mechanisms, not unified:
- **`x-api-key` header** (`AuthGuard.verify_api_key`) — used for the legacy/external API-key concept, mostly unused in current router wiring (grep shows it's defined but few routes actually depend on it directly vs. `get_current_user`).
- **`Authorization: Bearer <JWT>`** (`AuthGuard.get_current_user`) — what essentially every authenticated endpoint uses.
- **`AuthGuard.require_admin`** (added Domain 10) — `get_current_user` plus a role check; the single shared admin-gate dependency going forward. Three older hand-rolled per-router `_check_admin*` methods still exist (Domain 2/8 finding) and haven't been migrated to it.

## OpenAPI examples

Present on some request models (`example=1` on a few `Field(...)` calls) but not systematic. `openapi_url='/openapi.json'`, `docs_url='/docs'` — both live, `openapi.yaml` at repo root is generated output (`make openapi`), not hand-edited.
