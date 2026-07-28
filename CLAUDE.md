# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`semd-backend` is the FastAPI backend of SEMD ("Suspicious-URL Evaluation for Malicious Detection"). It is one of four independent git submodules of the parent SEMD project (backend / ML service / web frontend / browser extension) — see `../CLAUDE.md` at the repo root for the cross-service architecture and how this module talks to `semd-ml` over Redis. This file only covers what's inside `semd-backend/`.

## Setup and running

Python `3.12.x` (pinned via `.python-version`). Everything is driven through the `makefile` and `uv` — there is no venv-activation script anymore (the old `backend-working.sh`/`setup-config.sh` were consolidated into it):

```bash
make setup   # bootstrap config/backend.ini, config/redis.conf, docker/postgres.env + `uv add -r requirements.txt` && `uv sync`
make start   # podman compose -f docker/compose.yaml up -d --build --remove-orphans
make prod    # uv run python main.py prod
make worker  # uv run python -m workers.prediction_worker
make clean   # remove .venv and __pycache__
```
Run `make help` for the current target list. Since no `pyproject.toml`/`uv.lock` existed originally, `make setup`'s `install` step uses `uv add -r requirements.txt` (which creates `pyproject.toml` if missing) followed by `uv sync` rather than a bare `uv sync`.

Config is **not** `.env`-based despite the module having historically documented that — `config/settings.py` reads `config/backend.ini` via `configparser` (with hardcoded fallbacks), and `Settings` (a `pydantic-settings` `BaseSettings`) just wraps those values. `make config` (part of `make setup`) copies `config/backend.example.ini` → `config/backend.ini` and `config/redis.example.conf` → `config/redis.conf` (non-destructively — won't clobber an existing file), then extracts the Postgres/Redis credentials out of `backend.ini` to patch `config/redis.conf` and generate `docker/postgres.env`. Read the `config`/`install` targets in `makefile` before editing those generated files by hand.

Docker/Podman: `docker/compose.yaml` is the single stack entrypoint for backend + PostgreSQL + Redis. Docker assets are centralized under `docker/` (`backend.Dockerfile`, `redis.Dockerfile`, `postgres/init.sql`, `postgres.env`). The stack uses the local `semd-shared-network` bridge declared inside the compose file.

There is a `tests/unit/` suite using `unittest`. Lint/typecheck targets are wired through `make lint` and `make typecheck`.

`main.py` regenerates `openapi.yaml` from the live FastAPI app on every import (`app.openapi()` dumped to YAML at module scope). This means starting the app in *any* mode rewrites `openapi.yaml` — expect it to show as modified after a dev server run, and treat it as generated output rather than hand-editable.

## Architecture: layering

Strict one-directional dependency chain, one subpackage/module per domain (`auth`, `ml`, `prediction`, `report`, `setting`, `stat`, `dashboard`, `queue`):

```
routers/  →  control/  →  services/  →  models/db/ (SQLAlchemy models)
(FastAPI       (business    (DB / Redis /   models/ (Pydantic schemas) sit
 route defs)    logic)       third-party      alongside, used by all layers)
                             HTTP calls)
```

- `routers/*_route.py` classes all subclass `routers/base_route.py::BaseRoute`, which just wraps an `APIRouter` with `prefix`/`tags`/`responses` and exposes `get_router()`. Each router's `__init__` registers its endpoints via `self.router.post(...)(self.method)` rather than decorators, because the route handler is an instance method. `routers/__init__.py` is the single place all route classes are re-exported for `main.py` to `include_router()`.
- `control/*_control.py` — one `*Control` class per domain, instantiated per-request with a `db: AsyncSession` (plus usually `user_id`/`user`). This is where cross-cutting logic lives (e.g. `PredictionControl.predict()` resolves a default ML service if none given, logs usage, checks URL flags, and enqueues retraining — see `control/prediction_control.py`).
- `services/` — DB queries and external I/O. Some services are also directly instantiated as a module-level singleton (e.g. `prediction_service = PredictionService()` at the bottom of `services/prediction_service.py`) — don't assume every service is purely request-scoped.
- `models/*_model.py` — Pydantic request/response schemas. Every response model inherits `models/base_response_model.py::BaseResponseModel` (`status`/`message` fields); high fan-in on it is expected, not coupling debt.
- `models/db/entities.py` — all SQLAlchemy ORM models in one file, re-exported via `models/db/__init__.py`. `libs/types/enums.py` holds the shared string enums referenced across layers (`RoleType`, `FlagType`, `ServiceType`, `ReportStatusType`, `UsageLogType`, `ModelStageType`, `OAuthProviderType`) — check here before adding a new status/type string.

## Prediction dispatch: ML model vs third-party REST

A single `ServiceConf` row (`service_type` = `ML_MODEL` or `REST_API`) decides how a prediction request is fulfilled. `services/prediction_service.py::predict_with_service()` branches on this:
- `ML_MODEL` → `_predict_with_ml_model()` → `services/ml_service_client.py` (submits to the `ml_prediction_queue` Redis queue and polls `ml_result:{job_id}` — the cross-service hop into `semd-ml` described in the root `CLAUDE.md`).
- `REST_API` → `_predict_with_third_party()` → looks up the matching `ThirdServiceConf` row and runs it through `services/client/third_service_executor.py::ThirdServiceExecutor`, which builds the HTTP call generically from `config_json` (`body_template`, `url_template.path_params`/`query_params`) and maps the response via `response_mapping`/`mapping_json`. This is what backs the dynamically-registered Cloudflare Radar / Thai PhishTank integrations (`POST /setting/third-service`, payload shapes documented in `README.md`).

Both branches persist through `services/prediction_storage_service.py`; `control/prediction_control.py` wraps whichever branch ran with URL-flag checking and retrain-queue enqueueing so callers don't need to know which service type was used.

## Auth

`guard/auth_guard.py::AuthGuard` provides FastAPI dependencies:
- `verify_api_key` — requires `x-api-key` header.
- `verify_bearer_token` / `get_current_user` — requires `Authorization: Bearer <token>`, verifies via `services/auth_service.py::AuthService.verify_token()`, loads the `User` row.
- `verify_both` — requires both, for endpoints that need an API key identity *and* a logged-in user.

Same file also defines `get_db()` / `get_async_db()` — the sync/async SQLAlchemy session dependency generators used everywhere via `Depends(get_db)` / `Depends(get_async_db)`.

## Known duplication — use the `services/client/` versions

`services/postgres_client.py` and `services/redis_client.py` are earlier, now-stale copies of `services/client/postgres_client.py` and `services/client/redis_client.py` (the `client/` versions add async session support and are what `guard/auth_guard.py`, `control/third_service_control.py`, `services/queue_service.py`, and `services/prediction_service.py` import). **New code should import from `services.client.postgres_client` / `services.client.redis_client`.** The one exception already in the codebase is `workers/prediction_worker.py`, which still imports the old top-level `services.redis_client` — functionally harmless (same Redis, same settings) since each is an independent singleton, but don't copy that import path into new code.

## Adding a new domain (router/control/service/model)

Follow the existing four-file pattern for consistency: `models/<domain>_model.py` (+ `_request.py`/`_response.py` if needed) → `services/<domain>_service.py` → `control/<domain>_control.py` → `routers/<domain>/<domain>_route.py`, then register the route class in `routers/__init__.py` and `app.include_router(...)` in `main.py`. Stat/report sub-resources go under `routers/stat/` and `services/stats/` respectively rather than the flat top level.
