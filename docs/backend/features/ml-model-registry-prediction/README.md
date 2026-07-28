# Feature: ML Model Registry and Prediction (Domain 10)

## Critical finding, fixed: any MEMBER could redirect all production prediction traffic

`routers/ml/ml_route.py` (`/ml/models*`) manages `ModelRegistry` rows — MLflow run IDs, artifact URIs (`model_uri`, `scaler_uri`, `label_uri`, `selecter_uri`), stage, and which model is currently active/production. Before this pass, **every mutating endpoint required only `AuthGuard.get_current_user`** — any authenticated MEMBER could:

- `POST /ml/models` — register a new "model" row pointing at **arbitrary URIs** they supply.
- `POST /ml/models/{id}/promote` / `/activate` — make that (or any existing) model the active/production one.
- `POST /ml/models/{id}/deactivate` / `DELETE /ml/models/{id}` — take down or delete a legitimate model.
- `PATCH /ml/models/{id}/stage`, `PUT /ml/models/{id}` — arbitrary metadata/stage tampering.

Combined, this means any account — not just admins — could redirect every user's prediction traffic to a model of their choosing, or take the real model offline. This backend never loads the model artifact itself (confirmed in Phase 1 — inference happens in `semd-ml`), so the direct blast radius here is registry/routing control, not local code execution; but whatever `semd-ml` does when it loads a model by URI (Phase 1 flagged joblib/pickle-loading trust as a concern for that service) inherits whatever URI got registered here. This is arguably the single highest-impact finding in the audit — worse than the Domain 8 global-flag issue, since it controls the actual model backing every prediction rather than annotating one flag.

**Fixed**: `create_model`, `update_model`, `update_model_stage`, `promote_to_production`, `activate_model`, `deactivate_model`, `delete_model` (7 endpoints) now require `AuthGuard.require_admin`. Read-only endpoints (`list_models`, `get_model`, `get_production_model`) and the prediction endpoints (`predict_url`, `predict_batch`) remain any-authenticated-user — reading model metadata or requesting a prediction isn't privileged the way changing what model serves predictions is.

## New shared dependency: `AuthGuard.require_admin`

Added to `guard/auth_guard.py` because this domain needed real admin gating and none of the three existing hand-rolled `_check_admin*` methods (Domain 2's finding) were reusable outside their own router files. While wiring it up, found and fixed a real bug: `require_admin`'s inner `Depends(get_current_user)` (a bare name referenced inside the `AuthGuard` class body) bound to the raw `staticmethod` descriptor object, not the same callable `AuthGuard.get_current_user` resolves to via attribute access elsewhere — two different objects, which silently broke `app.dependency_overrides` in tests (and would affect FastAPI's per-request dependency-instance caching identically in production, though not correctness there since both objects do the same thing when actually called — the override-matching is what actually broke). Fixed by extracting `_verify_bearer_token`/`_get_current_user`/`_require_admin` to module-level functions and assigning them as `AuthGuard.x = staticmethod(_x)`, so the exact same function object is reachable both via the class attribute and via other functions' `Depends(...)` defaults. Verified empirically (see commit — checked `dep.dependency is AuthGuard.get_current_user` before and after).

The three existing duplicated `_check_admin*` methods (Domain 2 finding) are **not** migrated to use this new dependency in this pass — that's a separate, low-risk follow-up, not bundled here to keep this domain's diff focused on its own finding.

## Orphaned router wired up, not deleted

`routers/ml/ml_training_route.py::MLTrainingRouter` was completely unregistered dead code (not exported from `routers/ml/__init__.py`, never `include_router`'d) with zero auth on any endpoint if it ever had been wired up as originally written. Its underlying calls (`services/ml_service_client.py::submit_training_job`/`get_job_result`/`trigger_model_retraining`) are real, working, Redis-queue-backed implementations — not stubs — so this was a half-wired feature, not dead code, and wiring it up (rather than deleting working functionality) was the right call per the Phase 1 audit's own framing of the choice. Now registered at `/ml/training/{submit,result,retrain}`, gated to `AuthGuard.require_admin` (training/retraining are resource-intensive, privileged operations), and its error handling swept to the same pure-passthrough pattern as every other domain (no rollback/cleanup logic existed to preserve). Prefix normalized from the original `/api/v1/ml/training` (redundant `/api` — already the app's `root_path` — plus an unused `/v1` segment) to `/ml/training`, matching every other router's convention.

## Also fixed: `GET /ml/service` was the same broken-stub bug as Domain 9

`get_service` was `return None` against `response_model=MLServiceResponse` — identical pattern to the 32 Dashboard/Stat stubs (Domain 9): FastAPI's response validation has always turned this into an unconditional 500. Same fix applied: authenticated, honest `501` via `NotImplementedFeatureError`.

## Error-handling sweep

`ml_route.py` had **zero** `try/except` blocks — confirmed by direct read, nothing to sweep there. `ml_training_route.py`'s 3 endpoints had the standard `except Exception as e: raise HTTPException(500, detail=str(e))` pattern (pure passthrough, no cleanup) — removed, consistent with every other domain.

## Testing

- `tests/unit/test_ml_model_registry_permissions.py` (new, 3 cases): all 7 mutating endpoints reject non-admin (403) and unauthenticated (401) callers; `/ml/service` returns 501 instead of crashing.
- `tests/unit/test_ml_training_route.py` (new, 5 cases, from wiring the router): registered and reachable; requires auth; rejects non-admin; admin can submit; retrain rejects non-admin.

## Client-visible changes / OpenAPI

- `/ml/models*` mutation endpoints: now `403` for non-admin callers where they previously succeeded — documented, intentional security fix.
- `/ml/service`: `500` (crash) → `501` (honest) for authenticated callers, `401` for unauthenticated.
- New paths: `/ml/training/submit`, `/ml/training/result`, `/ml/training/retrain` (additive — previously unreachable at any path).
- OpenAPI diff: 0 removed, +5 paths (`/health/live`, `/health/ready` from earlier phases, plus the 3 new training paths).

## Migration / rollback

`git checkout -- routers/ml/ml_route.py routers/ml/ml_training_route.py routers/ml/__init__.py routers/__init__.py application.py guard/auth_guard.py tests/unit/test_ml_model_registry_permissions.py tests/unit/test_ml_training_route.py`. No DB/schema impact.
