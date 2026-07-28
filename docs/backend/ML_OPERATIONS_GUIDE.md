# ML Operations Guide

## What this backend does and doesn't do

This backend performs **no in-process ML inference and no training**. It manages model **metadata** (`ModelRegistry` rows: MLflow run IDs, artifact URIs, stage, scores) and dispatches prediction/training work to the separate `semd-ml` service over Redis queues, polling a result cache. Confirmed in Phase 1, held true through this entire refactor — nothing built or fixed in Domains 1-13 changed this boundary.

## Model registry lifecycle

1. `POST /ml/models` (**admin-only**, see `ADMIN_API_GUIDE.md`) — register a model's metadata after it's been trained/logged in MLflow elsewhere. This backend never validates that the artifact URIs actually point at anything real or trustworthy — that's `semd-ml`'s concern when it loads them.
2. `PATCH /ml/models/{id}/stage`, `POST /ml/models/{id}/promote` — move a model through its lifecycle stage, culminating in production.
3. `POST /ml/models/{id}/activate`\|`/deactivate` — take a model in/out of active rotation.
4. `GET /ml/models/production` — what's actually serving predictions right now, optionally filtered by algorithm.

All mutating operations here are admin-gated as of Domain 10 — previously, any authenticated MEMBER could point production at a model of their own choosing. If you were relying on member-level write access to this API, that's gone, deliberately.

## Prediction dispatch

```
POST /ml/predict or /prediction/predict
  -> SSRF/URL-safety check (Domain 5)
  -> push job to Redis (ml_prediction_queue)
  -> semd-ml worker picks it up, runs inference, pushes result to ml_result_queue
  -> workers/prediction_worker.py (this repo) caches the result: ml_result:{job_id}
  -> this backend polls that cache (now non-blocking as of Domain 12) until it appears or times out
```

Prediction requests block for up to 30s (single) / 60s (batch) waiting for `semd-ml` — as of Domain 12, this wait no longer blocks the ASGI event loop, so concurrent requests are no longer serialized behind each other during that wait.

## Training

`POST /ml/training/submit` (**admin-only**) — submits `service_conf_id`, `dataset_files` (a list of filenames — no upload, no validation; see below), optional `algorithms`/`run_name`. `POST /ml/training/result` polls for completion. `POST /ml/training/retrain` is a convenience wrapper around submit with an auto-generated retrain run name. This router was **completely unregistered and unauthenticated** before Domain 10 — it existed in the codebase but was unreachable at any URL; now live at `/ml/training/*`, admin-gated.

## Dataset management — does not exist

There is no dataset upload, validation, versioning, or "eligibility for retraining" logic anywhere in this backend. `dataset_files` in a training-job submission is a bare list of filename strings — this backend trusts the caller (an admin) to know what those filenames refer to in whatever storage `semd-ml` reads from. The retrain URL queue (`GET /queue/url`, admin-only) is also **not connected** to training-job submission — an admin currently has to manually bridge "URLs sitting in the retrain queue" to "the dataset_files list I'm submitting." See `docs/backend/features/dataset-retraining/README.md` for the full gap analysis and a recommendation for closing it.

## Audit trail — does not exist

Model activation/promotion/deletion, and training-job submission, have **zero audit logging** — no record of which admin did what, when. See `docs/backend/features/system-audit-logs/README.md`.
