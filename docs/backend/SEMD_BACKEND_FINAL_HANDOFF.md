# SEMD Backend — Final Handoff

Engagement: full-codebase audit and domain-by-domain refactor of `semd-backend`, 13 domains, executed against the Master Agent Prompt. This document is the top-level entry point; it summarizes and cross-references the 38 detail documents under `docs/backend/` rather than repeating them.

## 1. Final architecture summary

Unchanged shape, tightened contracts. Layering is exactly as documented in `../CLAUDE.md` and `CLAUDE.md`: `routers/ → control/ → services/ → database/`, with `models/` (Pydantic schemas) and `core/` (exceptions, error handlers, security, middleware, logging, health) cut across all layers. No layer was added or removed. What changed within that shape:

- A typed exception hierarchy (`core/exceptions.py::AppError` and subclasses) now carries almost all expected-failure paths that used to collapse into a generic `except Exception: raise HTTPException(500, str(e))`. Centralized handling in `core/error_handlers.py` converts these into a consistent RFC-7807-flavored response body — see `docs/backend/standards/ERROR_HANDLING.md`.
- SSRF defense (`core/security.py`) is now a mandatory pre-check on every URL-accepting prediction path: lexical validation plus real async DNS resolution with resolved-IP checking, closing the classic "domain looks fine, resolves to 169.254.169.254" bypass.
- Authorization gaps are closed at the three places they mattered most: report ownership/IDOR (Domain 2), GLOBAL-scope URL flags (Domain 8), and ML model registry mutation (Domain 10) — the last of these was the single most severe finding of the engagement, since it controlled what model actually serves production predictions.
- Two previously-unreachable or broken subsystems were fixed rather than left dead: the `/ml/training/*` router (existed in code, was never registered — Domain 10) and `DELETE /setting/third-service/{id}` (constructed an invalid response model on every call, a guaranteed 500 — Domain 6).
- One blocking-I/O defect in the request path was fixed: `services/ml_service_client.py`'s poll loop used `time.sleep` inside `async def` handlers, serializing all concurrent prediction requests behind each other for up to the poll timeout. Now `asyncio.sleep`, proven non-serializing by a concurrency test (Domain 12).

Nothing outside `semd-backend/` was modified. `semd-ml`, `semd-frontend`, `semd-extension` are separate git submodules with their own remotes; every place this audit found a plausible fix that would require coordinated changes there (extension-token exchange endpoint, job-payload schema versioning) was documented as a cross-repo gap rather than attempted unilaterally, per the SSRF/error-handling mandate's caution against unverifiable cross-boundary changes.

## 2. Repository tree (top level, post-refactor)

```
semd-backend/
├── application.py              # create_application(), router registration
├── main.py                     # entrypoint; regenerates openapi.yaml on import
├── config/                     # settings.py (pydantic-settings over backend.ini)
├── core/                       # exceptions, error_handlers, security (SSRF), middleware, logging, health
├── guard/                      # auth_guard.py — AuthGuard dependencies
├── routers/                    # one subpackage per domain, thin — see API inventory
├── control/                    # one *Control class per domain — business logic
├── services/                   # DB/Redis/HTTP I/O; services/client/ is the current, non-stale set
├── models/                     # Pydantic request/response schemas
├── database/                   # SQLAlchemy models.py, docker-compose, semd.db.sql
├── libs/types/enums.py         # shared string enums (RoleType, FlagType, ServiceType, ...)
├── workers/                    # prediction_worker.py — separate process, Redis consumer
├── tests/unit/                 # 19 files, 86 tests, unittest-based (no pytest)
├── docs/backend/               # this handoff, 13 feature docs, 7 standards docs, 6 database docs,
│                                 6 API guides, 5 ADRs, contracts/ (openapi before/after/diff)
└── makefile                    # setup / start / prod / worker / clean / openapi targets
```

## 3. Feature inventory (13 domains)

| # | Domain | Doc | Code changed? | Headline finding |
|---|---|---|---|---|
| 1 | Users/Roles/Permissions | `features/users-roles-permissions/` | Yes | Report IDOR — any user could edit/delete any other user's report |
| 2 | API Access Keys | `features/api-access-keys/` | Yes | 13 broad-exception sites swept; one deliberate `rollback()` kept and commented |
| 3 | Extension Access Codes | `features/extension-access-codes/` | Yes | Extension token stored in plaintext; also `UserModel` leaking 7 secret fields |
| 4 | URL Evaluation + SSRF | `features/url-evaluation/` | Yes | No SSRF defense at all pre-refactor; added lexical + DNS-resolution checks |
| 5 | Third-Party Detection Services | `features/third-party-detection-services/` | Yes | Response bodies/exception text leaking into error responses; delete endpoint always-500 |
| 6 | URL Reports | `features/url-reports/` | No (docs only) | Dataset-queue-eligibility gap documented, not fixed |
| 7 | URL Flags/Whitelist | `features/url-flags-whitelist/` | Yes | Any MEMBER could set a GLOBAL flag affecting every user's results |
| 8 | Dashboard/Statistics | `features/dashboard-statistics/` | Yes | All 24 endpoints were fabricating or silently wrong data; converted to explicit `501` |
| 9 | ML Model Registry/Prediction | `features/ml-model-registry-prediction/` | Yes | Any MEMBER could redirect production prediction traffic — most severe finding overall |
| 10 | Dataset/Retraining | `features/dataset-retraining/` | Yes | Retrain queue readable by any user; no dataset upload/validation exists at all |
| 11 | Background Workers/Redis | `features/background-workers-redis/` | Yes | Blocking `time.sleep` in async handlers serialized all concurrent prediction requests |
| 12 | System/Audit Logs | `features/system-audit-logs/` | No (docs only) | `ActivityLog` table exists, is never written to; 1-of-11 audit categories covered |
| 13 | Shared/infra + standards | `standards/`, `database/`, ADRs | Partial | Baseline mypy/ruff counts captured; `.env.example` added; no source-wide lint/type fix attempted |

Numbering above follows this document's own count (1-13); it maps to "Domain 2" through "Domain 13" in commit-level references because Domain 1 (authentication) was validated and accepted before this engagement's autonomous portion began.

## 4. API inventory

Full detail: `docs/backend/API_OVERVIEW.md`, `docs/backend/ADMIN_API_GUIDE.md`. Summary: 102 paths in the final OpenAPI document (up from 97 pre-refactor — the 5 new paths are `/health/live`, `/health/ready`, and the 3 previously-unregistered `/ml/training/*` routes). Full before/after/diff: `docs/backend/contracts/openapi.before.json`, `openapi.after.json`, `openapi.diff.md`.

Client-visible contract changes, consolidated (see `openapi.diff.md` §4 for the full breakdown of what is and isn't visible in the schema itself):
- **Breaking, intentional (security):** `UserModel` response schema loses 7 fields (`password_hash`, `gg_acc_token`, `gg_re_token`, `gh_acc_token`, `gh_re_token`, `twofa_secret`, `ex_acc_token`). New `422 UNSAFE_URL` rejections on URL-accepting prediction endpoints. New `403` on 4 endpoint groups previously reachable by any authenticated MEMBER (GLOBAL flags, ML model mutation, ML training, retrain queue read).
- **Non-breaking, additive:** `/health/live`, `/health/ready`, `/ml/training/*` (newly reachable, not newly built), 5 new fields on `MLPredictResponse`.
- **Non-breaking, corrective:** ~13+ sites where a 500 became the already-intended typed status code (400/401/403/404/409); `DELETE /setting/third-service/{id}` goes from always-500 to 200; 24 dashboard/stat endpoints go from fabricated-or-wrong data to explicit `501`.

## 5. Authentication model

`docs/backend/AUTHENTICATION_GUIDE.md` is the full guide. Two independent credential types, usable separately or together via `AuthGuard.verify_both`:
- `x-api-key` header — checked by `AuthGuard.verify_api_key`.
- `Authorization: Bearer <token>` — checked by `AuthGuard.verify_bearer_token` / `get_current_user`, verified through `services/auth_service.py`.

`guard/auth_guard.py` was restructured in Domain 9 (ML registry work) to fix a real bug: `Depends(get_current_user)` used as a class-body default bound to a different function object than `AuthGuard.get_current_user` accessed via the class attribute, because `staticmethod` descriptor access and direct name reference aren't the same object. This silently broke `app.dependency_overrides` for any test or caller relying on identity equality. Fixed by defining the three guard functions at module level and assigning them onto the class via `AuthGuard.verify_bearer_token = staticmethod(_verify_bearer_token)`, so both access paths now resolve to the same object — verified with `is` identity checks and the full test suite (78 passed at that point, 86 now).

`config/settings.py` still declares `JWT_SECRET`/`JWT_ALGORITHM` fields that are never referenced anywhere in the auth flow — dead config, documented in `.env.example`, not removed (removing a `pydantic-settings` field is a low-risk but out-of-scope cleanup not tied to any domain's charter).

## 6. Authorization model

`docs/backend/ADMIN_API_GUIDE.md` has the complete endpoint-by-endpoint table. Three roles: `MEMBER`, `ADMIN`, `SUPER_ADMIN` (`libs/types/enums.py::RoleType`; a 4th value `GUEST` is defined but dead — never checked anywhere). `AuthGuard.require_admin` (added Domain 9) is the shared `role in (ADMIN, SUPER_ADMIN)` dependency; three older hand-rolled equivalents in `routers/auth/user_route.py`, `routers/setting/system_config_route.py`, `routers/setting/access_key_route.py` remain un-migrated — functionally identical, just not consolidated, and left alone since consolidating them wasn't any domain's specific fix target.

Newly admin-gated in this engagement (previously reachable by any authenticated MEMBER): GLOBAL-scope URL flags (Domain 7), all ML model registry mutation and all of `/ml/training/*` (Domain 9), the retrain URL queue read (Domain 10).

Left open, explicitly flagged as ambiguous rather than fixed: `GET /report`, `GET /report/{id}` let any authenticated user list/view any other user's report — plausibly an intentional shared threat-intel view, plausibly a bug. Genuinely undeterminable from the code or available docs; a product-owner call, not an engineering one.

## 7. Database model

`docs/backend/database/README.md`, `er-diagram.md` (embedded Mermaid ER diagram), `table-dictionary.md` (all 13 tables, column-by-column), `indexes.md`, `migration-guide.md`, `transaction-boundaries.md`. No schema migrations were performed — all 13 domains' fixes are application-layer (authorization checks, exception handling, response shapes), not schema changes. Two findings recorded but deliberately not acted on:
- No Alembic or any migration tool exists; schema changes are applied by hand against `database/semd.db.sql`. Recommended adoption documented in `migration-guide.md`, not implemented (infrastructure decision, not a bug fix).
- `services/url_report_service.py::update_report` does two sequential, non-atomic `db.commit()` calls (report update, then audit-row insert) — a real inconsistency window, kept in scope only as documentation (`ADR-0003`) rather than fixed, since fixing per-service commit boundaries is a wide-blast-radius change spanning every domain, explicitly deferred to its own pass per the mandate's "don't combine unrelated changes" rule.

## 8. ML integration model

`docs/backend/ML_OPERATIONS_GUIDE.md` is the full guide. This backend does no in-process inference or training — it owns model *metadata* (`ModelRegistry` rows) and dispatches actual work to the separate `semd-ml` service over Redis (`ml_prediction_queue` / `ml_training_queue`, result caches `ml_result:{job_id}`). That boundary was confirmed unchanged throughout — nothing built here crosses it. What changed on this side of the boundary: model-registry mutation and training submission are now admin-gated (§6), the poll loop is now non-blocking (§9), and the SSRF check now runs before either dispatch path (`/prediction/predict` and `/ml/predict*` both call the same `reject_unsafe_urls()`).

## 9. Background-job architecture

`docs/backend/features/background-workers-redis/README.md`, `docs/backend/adr/0006-background-job-strategy.md`. The one functional defect found and fixed: `services/ml_service_client.py::get_job_result` (and its `predict_url_sync`/`predict_urls_sync` callers) polled Redis with `time.sleep()` inside `async def` route handlers with no thread/executor offload — this blocked the entire ASGI event loop for up to the request timeout (30-60s) per prediction request, serializing all concurrent traffic in that worker process behind whichever request was currently waiting. Converted to `asyncio.sleep`; proven non-serializing with a real concurrency test (`tests/unit/test_ml_service_client_async.py`, `asyncio.gather` timing assertion), not just asserted as fixed.

Deliberately not built (ADR-0006): payload schema versioning (job payloads carry no `schema_version`; `semd-ml` writes them, and this repo can't verify what shape it currently emits without cross-repo coordination) and dead-letter/retry handling (`workers/prediction_worker.py::process_result` silently drops a result on any processing failure — new infrastructure, not a bug fix, and a partial version would look more complete than it is).

## 10. Error-handling standard

`docs/backend/standards/ERROR_HANDLING.md` — full response shape and the 11-entry error-code registry. The approach taken across all 13 domains, per the mandate: inventory each domain's broad `except Exception` sites, check whether typed errors were being silently downgraded to 500, delete the broad catch where centralized handling already covers it, keep only catches doing real cleanup/rollback/logging (documented inline where kept — e.g. `create_extension_token`'s `db.rollback()`), and convert genuinely-expected failure modes to `AppError` subclasses. The "missing `except HTTPException: raise` guard" pattern the mandate asked to check for every domain was **not universal** — Domains 3 (access keys) and 6 (third-party services) already had it correct before this engagement touched them, confirming the mandate's "investigate, don't assume" instruction was warranted rather than a foregone conclusion.

## 11. Observability

`docs/backend/standards/OBSERVABILITY.md`. Structured JSON request logging and `/health/live` + `/health/ready` exist (Phase 3 infra, predates the 13 domains). No metrics aggregation, no tracing, no alerting exists — not built in this engagement, documented as a gap.

## 12. Validation results — final gate run

Run at the end of this engagement, against the final state of every domain:

| Gate | Result | Notes |
|---|---|---|
| Unit tests | **86/86 passed** | `uv run python -m unittest discover -s tests/unit -p "test_*.py"`, 19 files. Every fix in every domain has a characterization test; see `docs/backend/standards/TESTING.md` for the full inventory. |
| Typecheck (mypy) | **188 errors, 33 files** | Pre-existing baseline, unchanged by this engagement's fixes. Dominant pattern is `Column[T]` vs `T` from the legacy `Column(...)`-style SQLAlchemy models (not `Mapped[]`); see `docs/backend/standards/TYPE_SAFETY.md`. **This gate does not pass** and this engagement did not attempt to clear it — the mandate's fixes were scoped per-domain, not a codebase-wide type migration. |
| Lint (ruff) | **141 errors** | Same status — pre-existing baseline, not cleared. 128 are auto-fixable, but `ruff --fix` was empirically shown in this engagement to break a circular import (see `docs/backend/standards/PYTHON_STYLE.md`) by alphabetizing `routers/__init__.py`'s imports; blind `--fix` across the whole tree is not safe here without manual review of every touched file. |
| OpenAPI diff | Structural diff run (§4 / `openapi.diff.md`) | Corrects an earlier path-set-only method that missed the `UserModel` breaking change — see `openapi.diff.md` for why that correction matters. |
| App boot | Verified per-domain via test-suite startup (TestClient triggers app creation) | No standalone `uv run fastapi dev` smoke test was run as part of this final pass; each domain's test file already exercises app construction. |
| Live cross-service integration | **Not exercised** | No live Postgres/Redis/`semd-ml` instance was available in this environment. Nothing in this handoff should be read as claiming end-to-end integration was verified against real infrastructure — only unit-level and in-process (TestClient) behavior was validated. |

Read the mypy/ruff rows as: **tests are green, static-analysis baselines are not, and were never in scope to fix.** Don't report this gate as "passing" — it isn't, and the honest state is more useful to whoever picks this up than a false green checkmark.

## 13. Known limitations

- No live-infrastructure integration testing (Postgres/Redis/`semd-ml`) was possible in this environment — see §12.
- `GET /report`/`GET /report/{id}` cross-user visibility is undecided (§6).
- Dataset upload/validation/versioning does not exist at all; the retrain queue and training-job submission are not connected to each other (Domain 10 doc).
- Audit logging covers roughly 1 of 11 plausible event categories; the `ActivityLog` table is defined but never written to anywhere in the codebase (Domain 12 doc).
- Transaction-boundary inconsistency in `url_report_service.py` remains open (§7, ADR-0003).
- mypy/ruff baselines remain at 188/141 errors — pre-existing, not introduced or cleared here.
- Extension access-token has no validation/exchange endpoint anywhere in `semd-backend`, `semd-frontend`, or `semd-extension` as of this audit — the token is generated and hashed on issuance, but nothing was found that redeems it. Flagged as undeterminable requirement, not blocking, since it may be intentionally handled client-side in a way not visible from the backend alone.

## 14. Deployment instructions

Unchanged from `CLAUDE.md`/`../CLAUDE.md` — this engagement did not touch deployment tooling:
```bash
make setup   # bootstrap config, uv add -r requirements.txt && uv sync
make start   # dev: uv run fastapi dev main.py
make prod    # uv run python main.py prod
make worker  # uv run python -m workers.prediction_worker
```
Docker/Podman: `docker/compose.yaml` (API) + `database/docker-compose.database.yaml` (Postgres/Redis), both requiring the external `semd-shared-network` bridge (`podman network create semd-shared-network`, created once). No changes to any of these files were made in this engagement.

## 15. Rollback procedures

Every domain's changes are isolated to the files listed in its `docs/backend/features/*/README.md` — there is no cross-domain code coupling introduced by this engagement (verified: each domain's checkpoint listed its own file set, and no domain's fix depended on another domain's code changes except Domain 9's `AuthGuard` restructure, which Domain 9's own ML-registry admin-gating directly depends on). To roll back a single domain: revert the specific commit(s) covering that domain's file list; its tests (also isolated per domain in `tests/unit/`) will fail closed if reverted incompletely, rather than silently passing against stale code. The one exception to isolation: `guard/auth_guard.py`'s restructure (Domain 9) is a dependency for `require_admin`, which is used by Domains 7, 9, and 10's admin-gating — reverting `auth_guard.py` alone without also reverting those three domains' `Depends(AuthGuard.require_admin)` call sites will break authorization, not just fail to fix it. Roll those four back together if rolling back any of them.

## 16. Recommended future improvements

In priority order, based on severity and the gaps documented across all 13 domains:
1. Resolve the `GET /report` cross-user visibility question with the product owner (§6) — currently the largest undecided authorization question.
2. Build real audit logging (Domain 12 doc has a concrete recommendation: new audit table + `core/audit.py` helper) — currently zero visibility into who did what for any admin mutation.
3. Adopt Alembic or equivalent for schema migrations (`database/migration-guide.md`) before the next schema change, rather than continuing hand-applied DDL.
4. Coordinate with `semd-ml` maintainers on job-payload schema versioning and dead-letter handling (ADR-0006) — cannot be done unilaterally from this repo.
5. A dedicated, test-driven pass on transaction boundaries (ADR-0003) — inject forced failures between sequential commits, prove atomicity, don't fold it into unrelated domain work.
6. A deliberate `Mapped[]`/`mapped_column()` migration for SQLAlchemy models to address the dominant mypy error pattern (`docs/backend/standards/TYPE_SAFETY.md`) — large, mechanical, but genuinely reduces the 188-error baseline rather than working around it.
7. Close the dataset-upload/retrain-queue gap (Domain 10 doc) so "URLs sitting in the retrain queue" and "dataset_files submitted for training" aren't manually bridged by an admin.

## 17. Mobile scope confirmation

Per the master prompt's explicit instruction, mobile support is discontinued and was treated as out of scope throughout this engagement: nothing was implemented, restored, tested, or documented as mobile-specific. Where a shared API endpoint's history suggested past mobile usage, it was preserved (not removed) since the instruction was that shared APIs must not be removed merely because mobile once used them — removal decisions on such endpoints were left undone in every domain unless a different, mobile-unrelated reason (security, correctness) justified a change.
