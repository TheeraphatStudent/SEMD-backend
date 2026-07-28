# Testing Standard

## Framework and runner

Stdlib `unittest` (including `unittest.IsolatedAsyncioTestCase` for async code), **not pytest** — pytest is not a project dependency (confirmed absent from `pyproject.toml`/`uv.lock`, and unimportable even inside this project's own `.venv`, per Phase 1 audit). This was the pre-existing WIP test suite's own choice, kept deliberately rather than introducing a second test framework mid-refactor. Run via:

```bash
make test   # uv run python -m unittest discover -s tests/unit -p "test_*.py"
```

Current state: **86 tests, 19 files, all passing.** Zero pytest markers, fixtures, or plugins anywhere — nothing in this suite depends on pytest-only features.

## Test file inventory (what each one actually covers)

| File | Covers |
|---|---|
| `test_settings_redis.py` | Pre-existing (WIP). Settings env/ini precedence, Redis connection timeout behavior |
| `test_ml_prediction_service.py` | Pre-existing (WIP). `MLPredictionService` request/response contract mapping |
| `test_app_boot.py` | App factory boots, `/docs`/`/openapi.json`/`/health`/`/health/live`/`/health/ready` reachable, request-ID header present |
| `test_core_security.py` | 13 lexical SSRF-validator cases (scheme, credentials, private/loopback/metadata IPs, numeric-encoded hosts) |
| `test_core_error_handlers.py` | Error-shape contract: `AppError`→ typed shape, `HTTPException`→ `detail` preserved, unexpected exception → generic message (secret-leak regression guard), validation error → `errors` list |
| `test_auth_error_handling.py` | Domain 1 (auth) — the mangled-to-500 bug fix, generic-500-no-leak, successful-response shape unchanged |
| `test_access_key_error_handling.py` | Domain 3 — ownership-check 403 preserved, admin-gate 403, extension-token rollback preserved + hash-at-rest (Domain 4 extended this file) |
| `test_user_model_no_secrets.py` | Domain 4 — the 7 removed secret fields are actually absent from the schema, `model_validate` still works |
| `test_url_report_permissions.py` | Domain 2 — IDOR fix: non-owner blocked, owner can edit non-status fields, owner cannot self-approve status, admin can |
| `test_core_security_dns.py` | Domain 5 — DNS-resolution safety layer, mocked (no live network dependency) |
| `test_prediction_ssrf.py` | Domain 5 — SSRF validator proven wired into **both** URL-submission entry points (`PredictionControl` and `MLPredictionService`), not just built |
| `test_third_service_executor_errors.py` | Domain 6 — vendor secrets/connection details not leaked, redirect rejected not followed |
| `test_third_service_route_delete.py` | Domain 6 — the broken `status="success"` crash, regression guard |
| `test_url_flag_permissions.py` | Domain 8 — GLOBAL-flag privilege-escalation fix, 7 cases |
| `test_dashboard_stub_endpoints.py` | Domain 9 — spot-checks 401/501 across all 7 stat/dashboard routers |
| `test_ml_model_registry_permissions.py` | Domain 10 — all 7 model-mutation endpoints reject non-admin/unauthenticated |
| `test_ml_training_route.py` | Domain 10 — orphaned-router-now-wired: reachable, auth-required, admin-gated |
| `test_queue_route_permissions.py` | Domain 11 — retrain-queue privacy fix, admin-gated |
| `test_ml_service_client_async.py` | Domain 12 — proves the event-loop-blocking fix actually achieves concurrency (not just "doesn't crash") |

## What "characterization test" means in this codebase's practice

Every domain's security/behavior fix in this refactor was paired with a test that pins **both** directions: the fixed behavior (403/422/501/etc. now correct) **and** that legitimate/previously-correct behavior is unchanged (e.g. `test_auth_error_handling.py::test_successful_login_shape_unchanged`, `test_url_report_permissions.py::test_owner_can_update_non_status_fields`). This is what the mandate's "add characterization tests proving both directions" instruction meant in practice, applied per-domain rather than as a separate abstract testing pass.

## What's not covered

- **Repository/DB-integration tests against a real Postgres instance** — every test in this suite mocks the DB layer (`MagicMock`, `SimpleNamespace`, `FakeAsyncSession`) rather than exercising real queries, constraints, or transactions. No test database is configured in this environment. This means constraint violations, cascade behavior, and concurrent-update semantics are untested.
- **API integration tests using a live server** — `TestClient` (Starlette's in-process test client) is used throughout, which exercises the full FastAPI stack (middleware, dependency injection, response validation) but not real network I/O, real Redis, or real Postgres.
- **Security tests for expired/invalid/revoked JWTs, replayed refresh tokens** — not built in this pass; the auth-domain sample focused on the error-handling/status-code fix, not a full security-test matrix for token lifecycle.
- **ML-specific tests** (feature ordering, model/scaler compatibility, deterministic fixture predictions) — out of scope; this backend performs no in-process inference (confirmed in Phase 1), so these belong in `semd-ml`, not here.
- **Load/performance tests** for the Domain 12 concurrency fix beyond the one targeted `asyncio.gather` proof.

## Adding a new test

Follow the existing per-domain pattern: name the file `test_<domain-or-concern>.py`, use `unittest.TestCase` (sync) or `unittest.IsolatedAsyncioTestCase` (async), prefer mocking at the service/client boundary (`unittest.mock.patch`/`AsyncMock` — note `unittest.mock.patch` auto-detects async targets and substitutes `AsyncMock` automatically, no manual wrapping needed) over hitting real infrastructure. Run `make test` before considering a change complete.
