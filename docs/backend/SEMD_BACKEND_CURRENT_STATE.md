# SEMD Backend — Current-State Audit

Audited: 2026-07-15, working tree of `semd-backend` on branch `develop`, **including uncommitted changes** (per explicit scope decision — the tree is treated as ground truth, WIP is not reverted or ignored). Companion documents: `SEMD_BACKEND_TARGET_ARCHITECTURE.md`, `SEMD_BACKEND_REFACTOR_ROADMAP.md`.

This audit covers Phase 0 (repository discovery) and Phase 1 (current-state audit) per the SEMD backend refactoring mandate. No production code was changed to produce this document.

## Scope note: mobile

Grepped the entire backend (`routers/`, `models/`, `control/`, `services/`, `database/`) for mobile-specific signals (`mobile`, `device_token`, `push_notification`, `fcm`, `apns`, `device_regist`) — **zero matches**. No mobile-only endpoints, schemas, or auth flows exist in this codebase today. The one token-like feature that could be confused for mobile — `POST /setting/access-key/extension/token` and the `User.ex_acc_token`/`ex_acc_token_exp` columns — is for the **browser extension** (`semd-extension`), not mobile; naming and cross-repo usage confirm this. **Classification: not applicable — no mobile legacy code to deprecate in this module.**

---

## 1. Uncommitted working-tree changes (WIP, left as-is)

The tree carries in-flight, untested-in-CI but self-tested (via the new `tests/` dir) changes:

| File | Change |
|---|---|
| `config/settings.py` | Added `SettingsConfigDict(env_ignore_empty=True)` so a blank env var (e.g. unset `${REDIS_PASSWORD}` in compose) falls through to `backend.ini`/default instead of wiping a valid ini value. Removed `print(config)` (was printing parsed ini values, including secrets, to stdout on every import). |
| `services/redis_client.py`, `services/client/redis_client.py` | Added `socket_connect_timeout=5`, `socket_timeout=5` to the Redis client constructor (both copies, manually kept in sync) — fail fast instead of hanging on an unreachable Redis. |
| `models/model_registry_response.py` | `MLPredictResponse` gained `is_malicious`, `model_version`, `model_alias`, `feature_schema_version`, `prediction_time_ms`; `algorithm` gained a default. |
| `services/ml_prediction_service.py` | Populates the new `MLPredictResponse` fields from the ML worker's result payload. |
| `services/prediction_service.py` | `prediction_data.get('prediction', prediction_data.get('class', 'unknown'))` — tolerates the ML result using either key name for the predicted class. |
| `database/docker-compose.database.yaml`, `docker/compose.yaml`, `makefile` | Local dev workflow migrating from `uv run fastapi dev` to a podman-compose-first flow (`make start` now builds/runs both compose files); `docker/compose.yaml`'s broken `include: - path: './db/compose.yaml'` fixed to `'../database/docker-compose.database.yaml'` (CLAUDE.md documents this as previously broken — **the WIP fixes it**, so the CLAUDE.md note is stale as of this diff); Postgres healthcheck removed. |
| `README.md` | Documents the settings resolution order (env > ini > default) and container-vs-host Redis host resolution. |
| `tests/unit/*.py` (untracked, new) | 2 files, 11 `unittest`-based tests, all passing against current tree — see §3. |

**Correction to `CLAUDE.md`**: the module's own CLAUDE.md states "no test suite exists" and flags `docker/compose.yaml`'s `include` path as broken. Both are stale relative to this working tree — a test suite now exists (untracked) and the include path is fixed (uncommitted). Recommend updating CLAUDE.md once this WIP is committed.

---

## 2. Application startup and lifecycle

```mermaid
flowchart TD
    A[uvicorn / fastapi dev starts] --> B["import main -> module-level FastAPI() created"]
    B --> C[CORSMiddleware added: allow_origins=*, allow_credentials=False]
    C --> D[19 routers include_router'd]
    D --> E["app.openapi() computed and written to openapi.yaml on disk, every import"]
    E --> F[Application ready — no lifespan/startup/shutdown hooks]
```

Findings:
- **No FastAPI lifespan or `@app.on_event` handlers exist** (`main.py:1-142`, confirmed via grep — zero hits). Database and Redis clients are lazily constructed per-dependency (`guard/auth_guard.py`'s `get_db`/`get_async_db`) or as module-level singletons instantiated at import time (`services/prediction_service.py`, `services/client/redis_client.py`) — there is no explicit "verify DB/Redis reachable" step at boot, and no explicit connection cleanup at shutdown.
- **Side effect on import**: `main.py:90-92` calls `app.openapi()` and writes `openapi.yaml` to disk every time `main` is imported — this happens on every dev-server reload, every test that imports the app, and every `python -c "import main"`. This is documented behavior (per CLAUDE.md) but means `openapi.yaml` must be treated as **generated output**, not a source file — it will show as modified after any local run.
- **`GET /health` is not a real health check** (`main.py:56-64`) — it returns hardcoded `cpu_usage: '0%'`, `memory_usage: '0 / 16GB'`, `disk_usage: '0 / 512GB'` regardless of actual system or dependency state. It does not check DB or Redis connectivity. There is no `/health/live` or `/health/ready` split.
- **CORS is wide open**: `allow_origins=['*']` with `allow_credentials=False` (`main.py:35-42`) — credentials-false is the one mitigation preventing browsers from sending cookies cross-origin, but any origin can call the API (mitigated somewhat by the fact that auth is bearer-token/API-key based, not cookie-based, so `*` origin is lower-risk than it would be for a cookie-auth API — still worth tightening for a production target).
- `main.py:95-138` defines a `main()` CLI (`dev`/`prod` uvicorn launcher) that is **not what actually runs in Docker** — `docker/backend.dockerFile`'s `CMD` calls `uvicorn main:app` directly, bypassing this CLI entirely. Two separate "prod" code paths exist (the CLI's `prod` branch with `workers=4`, and the Dockerfile's plain `uvicorn main:app`) and they diverge (worker count, reload).

## 3. Request lifecycle

```mermaid
sequenceDiagram
    participant Client
    participant CORS as CORSMiddleware
    participant Router
    participant AuthGuard
    participant Control
    participant Service
    participant DB as Postgres/Redis

    Client->>CORS: HTTP request
    CORS->>Router: pass-through (no auth/logging middleware)
    Router->>AuthGuard: Depends(get_current_user / verify_api_key)
    AuthGuard-->>Router: User or 401
    Router->>Control: instantiate *Control(db, user_id, user)
    Control->>Service: call *_service methods
    Service->>DB: SQLAlchemy query / Redis command
    DB-->>Service: result
    Service-->>Control: domain data
    Control-->>Router: response model or raises HTTPException
    Router-->>Client: JSON response (try/except HTTPException wraps every handler)
```

Deviations from the target layered flow (`routers -> control -> services -> database`):
- **No request-ID / correlation-ID middleware exists** — nothing generates or propagates a request ID; `logging` calls (where they exist, e.g. `routers/prediction/prediction_route.py:11-13`) have no correlation to a specific HTTP request.
- **No logging middleware** — no per-request access log (method, path, status, duration) is emitted anywhere; the only `logging` usage found is ad hoc within a few route modules.
- Business logic mostly sits correctly in `control/*_control.py`, but **every router method individually wraps its call in `try: ... except Exception as e: raise HTTPException(500, detail=str(e))`** rather than routers being thin and letting a global handler catch unexpected errors — this is duplicated 61 times across the router layer (see §5) instead of centralized.

## 4. API inventory

Full inventory (107+ registered endpoints across 19 routers, plus 3 orphaned) captured during Phase 0 discovery. Key structural findings surfaced here; the complete per-endpoint table (method, path, router file, auth dependency, request/response schema) is preserved in the Phase 0 discovery notes and should be regenerated as `docs/backend/contracts/openapi.before.json` (see §4.4) rather than hand-maintained, since `main.py` already regenerates `openapi.yaml` from the live app.

### 4.1 Orphaned router — dead code

`routers/ml/ml_training_route.py` defines `MLTrainingRouter` (`/api/v1/ml/training/submit`, `/result`, `/retrain`) but:
- is **not exported** from `routers/ml/__init__.py` (only `MLRoute` is exported)
- is **never instantiated or `include_router`'d in `main.py`**
- has **zero `AuthGuard` dependency on any of its 3 endpoints** — if it were ever wired up as-is, it would be a fully unauthenticated write path.

**Status: unreachable dead code.** Requires clarification — either finish wiring it (with auth added) or delete it; do not leave it half-built and unauthenticated.

### 4.2 Stub routers — reachable but broken (32 endpoints)

`DashboardRoute` (8 endpoints) and all 6 `routers/stat/*` routers (24 endpoints, `ReportStatRoute`, `PredictionStatRoute`, `UserStatRoute`, `ApiKeyStatRoute`, `ThirdPartyStatRoute`, `UrlFlagStatRoute`) are registered in `main.py` and publicly reachable, but every handler body is a bare `pass` (implicitly returns `None`). Each declares a Pydantic `response_model`, so **every call to any of these 32 endpoints raises a FastAPI response-validation error** (`None` doesn't satisfy the declared schema) — they are broken at runtime, not merely unimplemented. **None of the 32 have any `AuthGuard` dependency either**, so today they're both unauthenticated and non-functional.

**Status: partially working = false; these are "declared, unauthenticated, and broken."** This is the single largest concrete gap in the "Dashboard and Statistics" (Feature 9) domain — Phase 4 for that feature is effectively greenfield implementation, not refactoring.

### 4.3 Working routers

`auth`, `ml` (models CRUD + predict, minus the orphaned training sub-route), `prediction`, `report` (+ `usage`), `setting` (`service_conf`, `access_key`, `system_config`, `third_service`, `url_flag`), `queue` all have real implementations behind `AuthGuard.get_current_user` (or, for a few, `verify_api_key`/`verify_both` — not exhaustively re-verified per endpoint in this pass; treat the Phase 0 per-endpoint table as the source of truth when re-derived into `openapi.before.json`). Admin-only sub-paths under `access_key` and `system_config` layer an additional in-router `_check_admin`/`_check_admin_permission` role check on top of `get_current_user`.

### 4.4 OpenAPI contract snapshot

Captured at `docs/backend/contracts/openapi.before.json` (97 paths). **Freshness verified**: grepped the captured JSON for `model_version`/`feature_schema_version` (fields only present on `MLPredictResponse` because of the uncommitted WIP diff to `models/model_registry_response.py`) — both present, confirming the snapshot reflects the current working tree (including WIP), not a stale pre-WIP schema. This is the correct baseline for `openapi.diff.md` once Phase 3/4 changes begin, consistent with the scope decision to audit the working tree as-is.

### 4.5 Full endpoint inventory (persisted from Phase 0 discovery)

All routers except `MLTrainingRouter` (orphaned, §4.1) are registered via `main.py:67-87`.

| # | Method | Path | Router file | Domain | Auth dependency | Request schema | Response schema |
|---|---|---|---|---|---|---|---|
| 1 | POST | /auth/register | routers/auth/auth_route.py:33 | auth | none (public) | RegisterRequest | RegisterResponse |
| 2 | POST | /auth/create | routers/auth/auth_route.py:39 | auth | get_current_user | CreateUserRequest | CreateUserResponse |
| 3 | POST | /auth/login | routers/auth/auth_route.py:45 | auth | none (public) | AuthLoginRequest | Union[TokenPairResponse, PreAuthResponse] |
| 4 | POST | /auth/login/2fa | routers/auth/auth_route.py:51 | auth | none (public, pre-auth token in body) | TwoFAVerifyRequest | TokenPairResponse |
| 5 | POST | /auth/login/provider | routers/auth/auth_route.py:57 | auth | none (public) | AuthLoginProviderRequest | Union[TokenPairResponse, PreAuthResponse] |
| 6 | POST | /auth/refresh | routers/auth/auth_route.py:63 | auth | none (public) | RefreshTokenRequest | TokenPairResponse |
| 7 | POST | /auth/logout | routers/auth/auth_route.py:69 | auth | none (public) | RefreshTokenRequest | BaseResponseModel |
| 8 | POST | /auth/2fa/setup | routers/auth/auth_route.py:75 | auth | get_current_user | none | TwoFASetupResponse |
| 9 | POST | /auth/2fa/enable | routers/auth/auth_route.py:81 | auth | get_current_user | TwoFAEnableRequest | BaseResponseModel |
| 10 | POST | /auth/oauth/device | routers/auth/auth_route.py:90 | auth | none (public) | OAuthDeviceCodeRequest | OAuthDeviceCodeResponse |
| 11 | POST | /auth/oauth/device/poll | routers/auth/auth_route.py:96 | auth | none (public) | OAuthDevicePollRequest | Union[TokenPairResponse, PreAuthResponse, BaseResponseModel] |
| 12 | POST | /auth/oauth/authorize | routers/auth/auth_route.py:102 | auth | none (public) | OAuthAuthorizationRequest | OAuthAuthorizationResponse |
| 13 | GET | /auth/callback/{provider} | routers/auth/auth_route.py:108 | auth | none (public) | Query(code,state) | Union[TokenPairResponse, PreAuthResponse] |
| 14 | GET | /auth/me | routers/auth/auth_route.py:114 | auth | get_current_user | none | UserModel |
| 15 | PUT | /auth/me | routers/auth/auth_route.py:120 | auth | get_current_user | UserUpdateRequest | UserModel |
| 16 | POST | /auth/me/reset-password | routers/auth/auth_route.py:126 | auth | get_current_user | PasswordResetRequest | BaseResponseModel |
| 17 | GET | /auth/users | routers/auth/user_route.py:36 | auth (admin-users) | get_current_user (+role check) | pagination | UserListResponse |
| 18 | POST | /auth/users | routers/auth/user_route.py:42 | auth (admin-users) | get_current_user (+role check) | AdminCreateUserRequest | UserResponse |
| 19 | GET | /auth/users/{user_id} | routers/auth/user_route.py:49 | auth (admin-users) | get_current_user (+role check) | none | UserResponse |
| 20 | PUT | /auth/users/{user_id} | routers/auth/user_route.py:55 | auth (admin-users) | get_current_user (+role check) | AdminUpdateUserRequest | UserResponse |
| 21 | POST | /auth/users/{user_id}/reset-password | routers/auth/user_route.py:61 | auth (admin-users) | get_current_user (+role check) | AdminPasswordResetRequest | BaseResponseModel |
| 22 | DELETE | /auth/users/{user_id} | routers/auth/user_route.py:67 | auth (admin-users) | get_current_user (+role check) | none | BaseResponseModel |
| 23 | GET | /ml/service | routers/ml/ml_route.py:33 | ml | none | none | MLServiceResponse (stub — `get_service` returns None) |
| 24 | POST | /ml/models | routers/ml/ml_route.py:36 | ml | get_current_user | ModelRegistryCreateRequest | ModelRegistryResponse |
| 25 | GET | /ml/models | routers/ml/ml_route.py:43 | ml | get_current_user | Query(algorithm,stage) | ModelRegistryListResponse |
| 26 | GET | /ml/models/production | routers/ml/ml_route.py:50 | ml | get_current_user | Query(algorithm) | ModelRegistryResponse |
| 27 | GET | /ml/models/{model_id} | routers/ml/ml_route.py:57 | ml | get_current_user | none | ModelRegistryResponse |
| 28 | PUT | /ml/models/{model_id} | routers/ml/ml_route.py:64 | ml | get_current_user | ModelRegistryUpdateRequest | ModelRegistryResponse |
| 29 | PATCH | /ml/models/{model_id}/stage | routers/ml/ml_route.py:71 | ml | get_current_user | ModelStageUpdateRequest | ModelRegistryResponse |
| 30 | POST | /ml/models/{model_id}/promote | routers/ml/ml_route.py:78 | ml | get_current_user | none | ModelRegistryResponse |
| 31 | POST | /ml/models/{model_id}/activate | routers/ml/ml_route.py:85 | ml | get_current_user | none | ModelRegistryResponse |
| 32 | POST | /ml/models/{model_id}/deactivate | routers/ml/ml_route.py:92 | ml | get_current_user | none | ModelRegistryResponse |
| 33 | DELETE | /ml/models/{model_id} | routers/ml/ml_route.py:99 | ml | get_current_user | none | (204, no body) |
| 34 | POST | /ml/predict | routers/ml/ml_route.py:105 | ml/prediction | get_current_user | MLPredictRequest | MLPredictResponse |
| 35 | POST | /ml/predict/batch | routers/ml/ml_route.py:112 | ml/prediction | get_current_user | MLBatchPredictRequest | MLBatchPredictResponse |
| 36 | POST | /prediction/predict | routers/prediction/prediction_route.py:29 | prediction | get_current_user | PredictionRequest (multipart: url/text_file/csv_file) | PredictionResponse |
| 37 | GET | /report | routers/report/report_route.py:20 | report | get_current_user | Query(skip,limit) | ReportListResponse |
| 38 | GET | /report/me | routers/report/report_route.py:26 | report | get_current_user | Query(skip,limit) | ReportListResponse |
| 39 | GET | /report/{report_id} | routers/report/report_route.py:32 | report | get_current_user | none | ReportResponse |
| 40 | GET | /report/{report_id}/history | routers/report/report_route.py:38 | report | get_current_user | none | ReportListResponse |
| 41 | POST | /report | routers/report/report_route.py:44 | report | get_current_user | UrlReportCreateRequest | ReportResponse |
| 42 | PUT | /report/{report_id} | routers/report/report_route.py:50 | report | get_current_user | UrlReportUpdateRequest | ReportResponse |
| 43 | GET | /report/usage/logs | routers/report/usage_route.py:50 | report/usage-log | get_current_user | Query(limit,offset) | List[UsageLogResponse] |
| 44 | GET | /report/usage/recent | routers/report/usage_route.py:56 | report/usage-log | get_current_user | Query(limit) | List[RecentActivityResponse] |
| 45 | GET | /report/usage/stats | routers/report/usage_route.py:62 | report/usage-log | get_current_user | none | UsageStatsResponse |
| 46-53 | GET | /dashboard/system-stat, /system-health, /system-performance, /third-party-stat, /url-flag-stat, /url-report-stat, /api-access-key-stat, /user-stat | routers/dashboard/dashboard_route.py:17-24 | dashboard | **none (unguarded)** | none | **all stub `pass` handlers — broken, confirmed by direct read** |
| 54 | GET | /setting/service/ | routers/setting/service_conf_route.py:20 | setting | get_current_user | none | List[ServiceConfModel] |
| 55 | GET | /setting/service/{service_id} | routers/setting/service_conf_route.py:27 | setting | get_current_user | none | ServiceConfModel |
| 56 | POST | /setting/service/{service_id}/activate | routers/setting/service_conf_route.py:34 | setting | get_current_user | none | ServiceConfModel |
| 57 | POST | /setting/service/{service_id}/deactivate | routers/setting/service_conf_route.py:41 | setting | get_current_user | none | ServiceConfModel |
| 58 | GET | /setting/service/active/list | routers/setting/service_conf_route.py:48 | setting | get_current_user | Query(service_type) | List[ServiceConfModel] |
| 59-71 | 13 endpoints | /setting/access-key/... (/me, POST "", /{id}/reset, /{id}/usage×3, /admin, POST /admin, PUT/DELETE /admin/{id}, /admin/{id}/usage×3, /extension/token) | routers/setting/access_key_route.py:39-135 | setting | get_current_user (+ `_check_admin` for `/admin*`) | AccessKeyCreateRequest / AccessKeyAdminCreateRequest / AccessKeyAdminUpdateRequest | AccessKeyResponse / AccessKeyListResponse |
| 72-74 | GET/GET/PUT | /setting/system-config, /{config_key}, /{config_key} | routers/setting/system_config_route.py:31-50 | setting | get_current_user (+ `_check_admin_permission`) | SystemConfigUpdateRequest | SystemConfigListResponse / SystemConfigResponse |
| 75-80 | 6 endpoints | /setting/third-service/, /{id}, /{id}/execute, /{id}/rest-api/test | routers/setting/third_service_route.py:25-73 | setting | get_current_user | ThirdServiceCreateRequest / ThirdServiceUpdateRequest / ThirdServiceExecuteRequest | ThirdServiceResponse / Dict[str,Any] / BaseResponseModel |
| 81-86 | 6 endpoints | /setting/url-flag, /me, /{flag_id}, POST "", PUT/DELETE {flag_id} | routers/setting/url_flag_route.py:30-70 | setting | get_current_user | UrlFlagCreateRequest / UrlFlagUpdateRequest | UrlFlagResponse / UrlFlagListResponse |
| — | — | /setting (no endpoints registered; `setQueueJob` method exists but unused) | routers/setting/setting_route.py | setting | n/a | n/a | near-empty stub file, not a live endpoint |
| 87 | GET | /queue/url | routers/queue/queue_route.py:26 | queue | get_current_user | none | QueueListResponse |
| 88-91 | GET×4 | /stat/report, /list, /trend, /detail | routers/stat/report_stat_route.py | stat | **none** | none | **stub `pass` — broken, confirmed by direct read** |
| 92-95 | GET×4 | /stat/prediction, /trend, /by-model, /detail | routers/stat/prediction_stat_route.py | stat | **none** | none | **stub — broken (pattern confirmed via report_stat_route + dashboard_route direct reads; same file structure)** |
| 96-99 | GET×4 | /stat/user, /activity, /role, /top | routers/stat/user_stat_route.py | stat | **none** | none | **stub — broken (same pattern)** |
| 100-103 | GET×4 | /stat/api-key, /usage, /trend, /endpoint | routers/stat/api_key_stat_route.py | stat | **none** | none | **stub — broken (same pattern)** |
| 104-107 | GET×4 | /stat/third-party, /services, /trend, /errors | routers/stat/third_party_stat_route.py | stat | **none** | none | **stub — broken (same pattern)** |
| 108-111 | GET×4 | /stat/url-flag, /trend, /detail, /category | routers/stat/url_flag_stat_route.py | stat | **none** | none | **stub — broken (same pattern)** |
| — | GET | / | main.py:44 | root | none | none | GetDefaultApiEndpoint |
| — | GET | /health | main.py:51 | root | none | none | GetDefaultHealthCheck — hardcoded fake values, see §2 |

**Orphaned (not counted above, not reachable):** `MLTrainingRouter` — `/api/v1/ml/training/submit`, `/result`, `/retrain` (`routers/ml/ml_training_route.py:38,63,80`) — zero auth guard, dead code (§4.1).

**Verification note on the stub-routes claim**: directly read `routers/dashboard/dashboard_route.py` and `routers/stat/report_stat_route.py` in full (confirmed every handler body is a bare `pass`, no `AuthGuard` dependency in any method signature), then independently grep-verified all 5 remaining `stat/*` files (`prediction_stat_route.py`, `user_stat_route.py`, `api_key_stat_route.py`, `third_party_stat_route.py`, `url_flag_stat_route.py`) each show exactly 4 `pass`-terminated handlers and zero `current_user` references — confirming all 32 stub endpoints independently, not just by pattern inference.

---

## 5. Error handling audit

| Error source | Current handling | HTTP status | Client response | Logged | Problem |
|---|---|---|---|---|---|
| Any unexpected exception in a router method | `except Exception as e: raise HTTPException(status_code=500, detail=str(e))` — repeated in **61 locations** across `routers/` | 500 | `{"detail": "<str(e)>"}` | **No** — no logging call accompanies these catches | **Information disclosure**: raw Python exception text (can include SQL fragment, file path, internal attribute names) returned directly to the client. Violates the completion gate "internal errors must not expose stack traces to clients." Also violates "expected client errors should not be logged as server failures" in the other direction — since nothing is logged at all, genuine 500s are invisible in logs. |
| Known business errors (not found, invalid input, forbidden) | Ad hoc `HTTPException(404/400/403, detail="...")` raised directly from `control/`/`services/` layers or routers — no typed application-exception hierarchy | varies (400/401/403/404) | plain `{"detail": "..."}` | No | No error-code registry; two different endpoints returning "not found" for different reasons are indistinguishable to a client parsing responses programmatically. |
| SQLAlchemy / DB errors | Not caught explicitly anywhere found — falls through to the generic `except Exception` above (if any exists in that call chain) or propagates as an unhandled exception (FastAPI's default 500 with debug-mode traceback, since `app = FastAPI(..., debug=settings.debug)` — **if `settings.debug` is `True` in any deployed environment, full tracebacks are shown**) | 500 | generic or DB error string | No | No dedicated DB-error mapping; `debug=settings.debug` is a live footgun if that setting is ever true outside local dev. |
| Redis errors | Same — no dedicated handling found | 500 | generic | No | Same as above. |
| ML service errors (queue timeout, worker unavailable) | `services/prediction_service.py`/`ml_service_client.py` raise `HTTPException(503, ...)` on ML queue timeout (per `prediction_route.py`'s declared `503: {"description": "ML service unavailable"}` response doc) — this is one of the few endpoints with a considered error contract | 503 | structured | No | Reasonably handled compared to the rest of the codebase — worth using as the model for other domains. |
| Global exception handler | **None registered** — `grep "@app.exception_handler\|add_exception_handler"` returns zero hits in the entire codebase | n/a | n/a | n/a | Every router must remember to catch and translate errors itself; there is no safety net, and (per above) 61 call sites do it inconsistently and insecurely. |

**Summary**: no centralized error handling exists at all. This is Phase 3's highest-value target — a single global exception handler plus a typed application-exception hierarchy would eliminate the 61-site duplication and close the `str(e)` leak in one change.

---

## 6. Type-safety audit

| Finding | Location(s) | Severity |
|---|---|---|
| `debug=settings.debug` passed straight into `FastAPI()` | `main.py:31` | Medium — not a typing issue per se, but combined with no environment-specific config validation, nothing prevents `debug=True` in a prod deployment |
| `Any` used in response/service typing | `services/prediction_storage_service.py`, `services/redis_client.py`, `services/client/third_service_executor.py`, `services/client/redis_client.py`, `routers/setting/access_key_route.py`, `routers/setting/url_flag_route.py`, `models/prediction_response.py`, `models/report_response.py`, `models/ml_response.py` | Low-Medium — `third_service_executor.py`'s use is defensible (it maps genuinely dynamic third-party JSON), but the response models (`prediction_response.py`, `report_response.py`, `ml_response.py`) using `Any` in a *public API response* schema means the OpenAPI contract can't describe those fields — clients get an untyped blob where a real schema should exist |
| `role`, `type`, `access_level`, `status`, `stage` columns stored as plain `String` in the ORM despite typed Python enums existing in `libs/types/enums.py` | `database/models.py` (`users.role`, `url_flag.type`/`access_level`, `url_report.status`, `model_registry.stage`) | Medium — only `service_conf.service_type` and `usage_log.type` use real Postgres `ENUM` columns; the rest rely entirely on application-layer validation, so a direct DB write (migration, manual fix, admin script) can insert an invalid value with no DB-level constraint to catch it |
| No `ForeignKey()`/`relationship()` anywhere in `database/models.py` (0 hits via grep) despite `database/semd.db.sql`'s raw DDL declaring real `REFERENCES ... ON DELETE CASCADE` constraints | `database/models.py` vs `database/semd.db.sql` | **High** — the ORM model is silently out of sync with the actual DB schema it's meant to represent. Joins are done manually (`.join(ServiceConf, ServiceConf.service_conf_id == ModelRegistry.service_conf_id)`) instead of via `relationship()`, and nothing in the ORM layer would catch a column rename or FK-target drift at type-check time (there's no type checker configured anyway — see below) |
| No type checker configured | repo-wide — no mypy/pyright section in `pyproject.toml`, no config file | High (process gap) | Every finding above is invisible to CI because there is no CI and no type-check step. This should be Phase 3's first concrete tooling addition. |
| No linter/formatter configured | repo-wide — no ruff/black/flake8 config; `.vscode/settings.json` only has cSpell + theme | Medium | Style is currently whatever each contributor's editor produces. |

---

## 7. Security audit

### 7.1 Authentication and secrets

| Area | Finding | Assessment |
|---|---|---|
| Password hashing | `passlib.CryptContext(schemes=['bcrypt'])` (`services/auth_service.py:6,20`) | Good — industry-standard, adaptive cost |
| Login failure messages | Generic `"Invalid username or password"` for both unknown-user and wrong-password cases (`services/auth_service.py:37-57`) | Good — no username enumeration via error text |
| JWT signing | `python-jose`, HMAC via `settings.auth_algorithm`/`settings.auth_secret_key` (`services/auth_service.py:60-71`) | Standard; algorithm and key strength depend on `backend.ini`/env config, not verified in this pass — confirm `auth_algorithm` isn't `none` and `auth_secret_key` has real entropy in deployed config |
| Dead dependency | `PyJWT>=2.8.0` declared in `pyproject.toml`/`requirements.txt` but **zero imports found anywhere** — `python-jose` is what's actually used | Low — housekeeping, remove the unused declared dependency |
| Refresh tokens | JWT with `jti` (UUID) + `type: refresh` claim; **stored server-side as `sha256(token)` hash**, not plaintext (`services/auth_service.py:74-90`) | Reasonable — matches "hashed refresh-token persistence" requirement. Revocation/rotation-on-use behavior not fully traced in this pass — verify `is_revoked` is actually checked and flipped on `/auth/refresh` and that reuse of an already-rotated token is rejected (replay prevention), before relying on this as proven |
| TOTP secret storage | `user.twofa_secret = secret` (`services/two_factor_service.py:29`) — **stored in plaintext**, no field-level encryption before persisting to `users.twofa_secret` | **Finding: TOTP secrets are stored unencrypted at rest.** A DB read (backup leak, SQL injection, insider access) directly yields every user's live TOTP seed, defeating 2FA silently. Should be encrypted at rest (app-level envelope encryption or DB-level column encryption) before Phase 4's Authentication feature work is called done. |
| OAuth state (CSRF) | `state = secrets.token_urlsafe(32)` is generated and returned to the client at `/auth/oauth/authorize` (`control/auth_control.py:208-224`). Checked both files in the callback path — `services/oauth_service.py` only ever *sends* `state` outbound when building the provider authorization URL (lines 100, 203), and `control/auth_control.py`'s `handle_oauth_callback` (line 267+) accepts `state` from the callback query param with no stored-state lookup or comparison found in either file | **Finding: OAuth state parameter is generated but not verified on callback**, i.e., CSRF protection for the OAuth login flow is not actually enforced end-to-end as implemented. Needs either a server-side state store (Redis, short TTL) checked at callback time, or removal of the unused state machinery if it's intentionally deferred to the client. |
| Extension access token | 6-character alphanumeric (`string.ascii_letters + string.digits`, `secrets.choice`, `routers/setting/access_key_route.py:366-367`) stored **in plaintext** in `users.ex_acc_token` (not hashed, unlike API access keys below) | **Finding: inconsistent secret handling** — API access keys are properly sha256-hashed at rest (see below), but the extension token is stored in cleartext. 6 chars from a 62-character alphabet is ~35.7 bits of entropy — with no rate limiting on the exchange endpoint (see §7.3), this is brute-forceable in a feasible number of requests against a single account if the endpoint isn't otherwise protected. Recommend hashing at rest (matching the access-key pattern) and lengthening the code and/or adding rate limiting. |
| API access keys | Generated via `secrets.token_urlsafe(32)`, only `sha256(raw_key)` persisted (`services/access_key_service.py:20-27`); raw key returned once at creation | Good — matches "store only a secure hash," "display key once" requirements |
| ReCAPTCHA | **Not implemented anywhere** — zero references to "recaptcha" found in the codebase, despite the parent-project domain list mentioning it | Per instructions: confirm every domain from actual code, don't assume docs reflect reality. **ReCAPTCHA is aspirational/undocumented-elsewhere, not present in this module today.** Not a vulnerability, but the target architecture doc should not assume it exists. |

### 7.2 Injection / SSRF / URL handling

- **This backend never fetches user-submitted URL content itself.** Prediction flow (`routers/prediction/prediction_route.py` -> `control/prediction_control.py` -> `services/prediction_service.py`/`services/ml_prediction_service.py`) only forwards the URL **string** to either (a) the `ml_prediction_queue` Redis queue, consumed by the separate `semd-ml` service (out of scope for this audit — feature extraction/fetching behavior there must be audited separately), or (b) `services/client/third_service_executor.py`, which builds an outbound `httpx` request to an **admin-configured** third-party detector (Cloudflare Radar, Thai PhishTank) using the submitted URL as a template parameter.
- **No URL validation, normalization, or scheme allow-listing exists anywhere in this backend** (`PredictionRequest.url` — no validator found restricting scheme/format; confirmed via grep for private-IP/loopback/metadata/scheme-checking logic across `control/` and the prediction services — zero hits). Practically:
  - The direct SSRF blast radius from *this* service is low, since it doesn't fetch URLs itself — but it also does **zero input sanitization** before handing the raw string to (a) a Redis queue payload consumed by another service, and (b) a third-party HTTP request template. Neither `javascript:`, `file:`, `data:`, embedded-credential (`http://user:pass@host`), nor malformed/encoded-host URLs are rejected before reaching those downstream consumers.
  - **This is a real, if indirect, SSRF/injection exposure**: it pushes the entire burden of "is this URL safe to act on" onto `semd-ml` and onto whatever the third-party detector's API tolerates, with no defense-in-depth at the boundary where the URL first enters the system. The mandate's SSRF requirements (reject loopback/private ranges/link-local/metadata endpoints/unsupported schemes/embedded credentials/encoded hosts) are **not met at this layer today**.
- `services/client/third_service_executor.py` builds requests generically from admin-authored `config_json` (`body_template`, `url_template`) — this is admin-controlled configuration, not directly user input, so the injection surface there is lower-privilege (requires an authenticated admin to misconfigure), but still worth noting the executor does no allow-listing of the resulting outbound host either.
- No `requests`/`httpx`/`urlopen` calls found operating on **arbitrary uncontrolled hosts** outside of `oauth_service.py` (fixed provider URLs — Google/GitHub, not user input) and `third_service_executor.py` (admin-configured base URL + user-influenced path/query params).

### 7.3 Rate limiting, CORS, misc

- **No rate limiting exists anywhere** — grep for `rate.?limit`/`slowapi` across the codebase returns zero hits. This applies to login, TOTP verification, refresh-token exchange, extension-token exchange, and prediction endpoints alike. Combined with the extension-token entropy finding above, this is the most actionable gap.
- **CORS**: `allow_origins=['*']`, `allow_credentials=False` (see §2) — acceptable for a bearer-token API but worth tightening to a real origin allow-list for the target architecture.
- **Debug mode**: `app = FastAPI(..., debug=settings.debug)` (`main.py:31`) — verify this resolves to `False` in every non-local environment; not independently confirmed in this pass since it depends on runtime config (`backend.ini`/env), which varies per deployment.
- **File/dataset upload handling**: `routers/prediction/prediction_route.py` accepts `text_file`/`csv_file` multipart uploads for batch prediction (`_extract_urls`) — file-size limits, content-type validation, and path-traversal exposure for these uploads were not verified in this pass and should be checked explicitly before Phase 4 work on the Prediction feature.
- **Pickle/joblib deserialization**: not applicable to this repo directly — no model artifacts are ever loaded here (see §8); that risk lives entirely in `semd-ml`.

### 7.4 Security findings summary (by severity)

| Severity | Finding |
|---|---|
| High | No SSRF/scheme/private-IP validation on user-submitted URLs before they reach downstream queue/third-party consumers |
| High | Global exception handler leaks raw `str(exception)` to clients in 61 call sites |
| High | TOTP secrets stored in plaintext at rest |
| Medium | OAuth `state` CSRF parameter generated but not verified on callback |
| Medium | Extension access token stored in plaintext (unlike API keys) and low-entropy (6 chars), with no rate limiting on the exchange endpoint |
| Medium | No rate limiting anywhere in the API |
| Low | Unused `PyJWT` dependency declared alongside actually-used `python-jose` |
| Low | `debug=settings.debug` wired straight to `FastAPI()` with no environment-specific enforcement verified |
| Requires clarification | File/CSV upload validation (size, type, path traversal) for batch prediction not verified |

---

## 8. ML integration audit

**This backend performs no in-process ML inference, no model loading, and no training.** All compute is externalized to the separate `semd-ml` service. Flow:

```mermaid
sequenceDiagram
    participant Client
    participant PredictionRoute
    participant PredictionControl
    participant MLServiceClient
    participant Redis
    participant SemdML as semd-ml worker (external)
    participant PredictionWorker as workers/prediction_worker.py

    Client->>PredictionRoute: POST /prediction/predict
    PredictionRoute->>PredictionControl: predict(urls, service_id)
    PredictionControl->>MLServiceClient: predict_url_sync(url, model_id, timeout)
    MLServiceClient->>Redis: push_to_queue("ml_prediction_queue", job)
    MLServiceClient->>Redis: poll ml_result:{job_id} (blocking time.sleep loop)
    SemdML-->>Redis: BLPOP ml_prediction_queue, run model, push ml_result_queue
    PredictionWorker->>Redis: BLPOP ml_result_queue
    PredictionWorker->>Redis: SET ml_result:{job_id} (ttl 3600)
    MLServiceClient-->>PredictionControl: cached result (or timeout -> 503)
    PredictionControl-->>Client: PredictionResponse
```

Findings:
- `services/model_registry_service.py`/`control/model_registry_control.py` manage only **metadata** (MLflow run IDs, artifact URIs, stage, scores) in the `model_registry` Postgres table — no model object is ever instantiated in this codebase. "Model loading per request vs. cached singleton" does not apply here; that question belongs entirely to `semd-ml`'s audit.
- **Blocking synchronous poll inside an async handler**: `MLServiceClient.get_job_result()` uses `time.sleep(poll_interval)` in a loop (`services/ml_service_client.py:100-116`), and `predict_url_sync`/`predict_urls_sync` are called directly from `async def` FastAPI route handlers without `asyncio.to_thread`/`run_in_executor`. **This blocks the event loop for up to the poll timeout (30s single-predict, 60s batch) on every prediction request**, serializing concurrent request handling in that worker process. This is a real throughput problem, not just a style issue — it should be near the top of Phase 3/4 priorities for the Prediction feature.
- **Duplicated Redis client in the worker**: `workers/prediction_worker.py:15` imports the stale `services/redis_client.py` rather than the canonical `services/client/redis_client.py` used everywhere else (`ml_service_client.py`, `queue_service.py`). Same Redis instance/config underneath (both read `config.settings.settings`), so not a functional bug today, but a maintainability risk — confirmed by the uncommitted diff needing to apply the identical socket-timeout fix to both copies by hand.
- Job payloads pushed to Redis are plain dicts (not versioned/schema'd) — no explicit job-payload versioning was found, which the mandate's "use serializable, versioned job payloads" requirement calls out directly as a target-state requirement, not a current one.
- Retraining: `services/queue_service.py` exists for a `ml_training_queue`/retrain path; not deeply audited in this pass given the current-state doc's focus — flag for closer inspection in Phase 4's Training/Dataset feature work.

---

## 9. Database audit

Engine: **PostgreSQL**, confirmed via `psycopg2-binary`/`asyncpg` drivers and `database/docker-compose.database.yaml` (`postgres:latest` image) — not inferred from documentation.

No migration tool (no Alembic). Schema is bootstrapped via `database/semd.db.sql` (raw DDL, mounted as a Postgres container init script) with a `Base.metadata.create_all()` fallback in `PostgresClient.init_db()`. **This is a real gap**: schema changes have no reproducible migration path — see §6's finding that the SQL DDL and the SQLAlchemy models have already drifted (FK constraints exist in one, not the other).

### 9.1 Tables (13 total, recounted directly from `database/models.py` class definitions)

| Table | PK | Notable columns | FK enforcement |
|---|---|---|---|
| `users` | `user_id` | `username`/`email` unique, `password_hash`, `role` (plain string), `gg_*`/`gh_*` OAuth tokens, `twofa_secret`/`is_2fa_enabled`, `ex_acc_token`(+exp) | n/a (root table) |
| `refresh_tokens` | `refresh_tokens_id` | `user_id`, `token_hash` (unique), `jti` (unique), `expires_at`, `is_revoked` | `semd.db.sql`: `user_id REFERENCES users(user_id) ON DELETE CASCADE`; **not declared in `database/models.py`** |
| `service_conf` | `service_conf_id` | `user_id`, `service_type` (**real Postgres ENUM**), `is_active`, `config_uri`, `config_json` | Same drift as above |
| `model_registry` | `model_registry_id` | `service_conf_id` (unique), `stage` (plain string), `mlflow_run_id`, artifact URIs, score columns (`Numeric(5,4)`) | Same drift |
| `access_key` | `access_key_id` | `user_id`, `access_key_hash`, `is_active`, `usage_limit`, `expired_at` | Same drift |
| `prediction` | `prediction_id` | `user_id`, `url`, score columns (`Numeric(10,2)`), `is_malicious`, `predict_class` | Same drift |
| `url_flag` | `url_flag_id` | `user_id`, `url`, `type` (plain string, default `BENIGN`), `access_level` (plain string, default `PRIVATE`) | Same drift |
| `url_report` | `url_report_id` | `user_id`, `url`, `categories`, `status` (plain string, default `PENDING`), `remark` | Same drift |
| `activity_log` | `activity_log_id` | `user_id`, `method`, `endpoint`, `request_id` (unique), `client_ip`, `client_agent`, `response` | Same drift |
| `usage_log` | `usage_log_id` | `service_id`, `access_key_id`, `prediction_id`, `type` (**real Postgres ENUM**) | Same drift |
| `third_service_conf` | `third_service_conf_id` | `service_conf_id` (unique), `base_url`, `http_method`, `headers_json`/`config_json`/`mapping_json` | Same drift |
| `url_reported` | `url_reported_id` | `url_report_id`, `user_id`, `action`, `old_status`, `new_status`, `remark` — audit-history table for `url_report` state transitions | Same drift |
| `system_config` | `system_config_id` | `config_key` (unique), `config_value`, `description` | n/a |

**Core finding: `database/models.py` declares zero `ForeignKey()`/`relationship()` across all 12 tables**, while `database/semd.db.sql`'s DDL declares real `REFERENCES ... ON DELETE CASCADE` constraints on most of them. The database itself enforces referential integrity (since it's bootstrapped from the SQL file); the ORM layer the application code actually uses does not model it, so joins are manual (`.join(Model, Model.fk_col == Other.fk_col)`) and Python-level code gets no static or runtime protection against referencing a stale/renamed column.

### 9.2 Enum storage

`libs/types/enums.py` defines 8 Python enums: `RoleType`, `FlagType`, `ACLType`, `ReportStatusType`, `UsageLogType`, `ServiceType`, `ModelStageType`, `OAuthProviderType`. Only `ServiceType` (`service_conf.service_type`) and `UsageLogType` (`usage_log.type`) are backed by real Postgres `ENUM` columns — the other six are validated only at the application/Pydantic layer, with plain `String` columns underneath.

### 9.3 ER diagram (as-implemented, informal FKs shown as inferred from column naming + `semd.db.sql`)

```mermaid
erDiagram
    USERS ||--o{ REFRESH_TOKENS : owns
    USERS ||--o{ SERVICE_CONF : configures
    USERS ||--o{ ACCESS_KEY : owns
    USERS ||--o{ PREDICTION : requests
    USERS ||--o{ URL_FLAG : defines
    USERS ||--o{ URL_REPORT : submits
    USERS ||--o{ ACTIVITY_LOG : generates
    USERS ||--o{ URL_REPORTED : acts_on
    SERVICE_CONF ||--o| MODEL_REGISTRY : registers
    SERVICE_CONF ||--o| THIRD_SERVICE_CONF : configures
    ACCESS_KEY ||--o{ USAGE_LOG : tracked_by
    SERVICE_CONF ||--o{ USAGE_LOG : tracked_by
    PREDICTION ||--o{ USAGE_LOG : tracked_by
    URL_REPORT ||--o{ URL_REPORTED : has_history
```

---

## 10. Type/lint/test tooling status (honest baseline — do not fabricate passing gates)

| Check | Command | Status |
|---|---|---|
| Unit tests | `uv run python -m unittest discover -s tests/unit -p "test_*.py"` | **11/11 pass** (pre-existing WIP tests, verified during Phase 0) |
| pytest | n/a | **Not installed, not a dependency.** Tests use stdlib `unittest`. |
| Type checker | n/a | **Not configured.** No mypy/pyright config anywhere in the repo. |
| Linter/formatter | n/a | **Not configured.** No ruff/black/flake8 config. |
| OpenAPI contract snapshot | n/a | **Not yet captured** — `openapi.before.json` does not exist yet; `openapi.yaml` at repo root is live/current but in YAML, and is regenerated (not preserved) on every app import. |
| Migrations | n/a | **No migration tool.** Schema managed via raw SQL init script + `create_all()` fallback. |

Per the mandate's "do not hide failed validation commands" rule: type-check, lint, and pytest-based test gates are reported here as **not present**, not as "failed" — there is nothing to run yet. Setting these up is explicitly Phase 3 scope (Foundation Standardization), not something to fabricate now.

---

## 11. Carry-forward action items for Phase 2+

1. Capture `docs/backend/contracts/openapi.before.json` from the live app before any Phase 3/4 code change.
2. Centralized error handling (§5) and the `str(e)` leak are the highest-leverage single fix — eliminates 61 duplicated, insecure call sites at once.
3. SSRF/URL-validation gap (§7.2) needs a decision on which layer owns it — this backend (input boundary) vs. `semd-ml`/third-party executor (fetch boundary) — likely both, defense-in-depth.
4. TOTP plaintext storage and OAuth state-not-verified (§7.1) are concrete, scoped security fixes for the Authentication feature (Phase 4, Feature 1).
5. Stub Dashboard/Stat routers (32 endpoints, §4.2) and the orphaned ML training router (§4.1) need explicit product decisions (implement vs. remove) before Phase 4 reaches those features — they are not "existing behavior to preserve," they're currently broken or unreachable.
6. ORM/DDL foreign-key drift (§9.1) should be resolved (add `ForeignKey()`/`relationship()` to `database/models.py`) early, since every feature's repository layer work in Phase 4 will otherwise keep hand-rolling joins against an under-specified model.
