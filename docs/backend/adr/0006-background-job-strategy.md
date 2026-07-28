# ADR 0006: Fix event-loop-blocking poll; defer payload versioning and dead-letter handling

## Status
Accepted

## Context
`services/ml_service_client.py::get_job_result()` polled the Redis result cache with a blocking `time.sleep(poll_interval)` loop, called directly from `async def` FastAPI route handlers (`services/ml_prediction_service.py`, `services/prediction_service.py`, `routers/ml/ml_training_route.py`) with no `asyncio.to_thread`/`run_in_executor` wrapper. This blocked the entire ASGI event loop for up to the request timeout (30-60s) on every prediction request, serializing all concurrent request handling in that worker process. Flagged in Phase 1 (`SEMD_BACKEND_CURRENT_STATE.md` §8), left open through Domains 1-11, closed in Domain 12.

Separately, the master prompt requires "serializable, versioned job payloads" and dead-letter/retry handling for background job processing. Neither exists: job payloads (`services/ml_service_client.py`'s `job_data` dicts, `workers/prediction_worker.py`'s `result_data`) carry no `schema_version` field, and `workers/prediction_worker.py::process_result` silently drops a result on any processing failure (catches, logs, returns `False`, caller ignores the return value).

## Decision
1. Convert `get_job_result`, `predict_url_sync`, `predict_urls_sync` to `async def` using `asyncio.sleep`; update the three call sites to `await`. Keep the `_sync` naming (describes the request/response contract — caller gets a completed result, not a job handle — not the execution model), to avoid an unnecessary rename across every call site and test mock.
2. Do **not** add payload schema versioning in this pass. The payload is written by `semd-ml`, a separate repository this session cannot modify — unilaterally adding strict validation on the read side risks rejecting real production messages if the two repos' field assumptions ever drift, without any way to verify compatibility against `semd-ml`'s actual current output shape.
3. Do **not** build dead-letter/retry handling in this pass. This is new infrastructure (a dead-letter queue, a retry policy, alerting on repeated failures), not a bug fix — building a partial version risks looking more complete than it is.

## Alternatives rejected
- **Rewrite `services/client/redis_client.py` to use `redis.asyncio` throughout**, making every Redis call (not just the poll sleep) non-blocking. Rejected as out of scope for this fix: the deliberate `poll_interval` sleep was the dominant blocking cost (up to 60× 0.5s per request); individual `get_cache()` GETs are sub-millisecond and not the actual problem. A full async-Redis-client migration touches every caller across the codebase for a proportionally small additional gain.
- **Add payload versioning unilaterally and hope `semd-ml` already sends a compatible shape.** Rejected: no way to verify from this repo alone; a wrong guess breaks real prediction traffic silently.

## Consequences
- Concurrent prediction requests no longer serialize behind each other during the ML-service wait — proven with a concurrency test (`tests/unit/test_ml_service_client_async.py`), not just asserted.
- No client-visible contract change: same response shape, same timeout semantics, only the waiting mechanism changed.
- Payload versioning and dead-letter handling remain open, documented gaps (`docs/backend/features/background-workers-redis/README.md`) — a genuine cross-repo coordination requirement and a scoped infrastructure build respectively, neither appropriate to rush in this pass.
