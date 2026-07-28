# Feature: Third-Party Detection Services (Domain 6)

## Scope note

This "feature" spans two routers in the actual codebase: `routers/setting/service_conf_route.py` (generic service configuration — `ServiceConf`, shared by both `ML_MODEL` and `REST_API` service types) and `routers/setting/third_service_route.py` (REST_API-specific detail — `ThirdServiceConf`: base URL, HTTP method, headers, body/response mapping templates). Both audited here.

## Findings, ranked by what a caller actually sees

### 1. Fixed — error detail leaking past the resource owner (real severity, not theoretical)

`services/client/third_service_executor.py` is called from **two** places with very different privilege contexts:

- `control/third_service_control.py::execute()`/`test_execute()` — ownership-gated (`get_third_service_by_user` verifies the caller owns the `ThirdServiceConf` before touching it).
- `services/prediction_service.py::_predict_with_third_party()` — reachable from `/prediction/predict` by **any authenticated MEMBER**, for whichever `REST_API`-type service is configured as active. The caller here does not own or administer the third-party integration at all.

Before this pass, the executor's exception handlers put raw `str(e)` (connection errors — internal hostnames, proxy addresses) and `e.response.text` (the vendor's raw response body — which can include secrets like `vendor_api_key=...` depending on how the vendor formats errors) directly into the `HTTPException.detail`, which propagated unmodified through `PredictionControl` and `prediction_route.py` (both clean passthrough, no wrapping) straight to the requesting MEMBER. Fixed: real detail is logged server-side (`logger.warning`/`logger.error` with `exc_info`); the caller — admin or MEMBER, either path — now gets a generic `ExternalServiceError`/`ServiceUnavailableError` (502/503) with a safe, non-identifying message. A stray `print(e)` debug statement was also removed.

Also fixed: the redirect-rejection and response-size-guard checks (added in Domain 5's pull-forward) were themselves `HTTPException` raises sitting *inside* the same `try` block as the generic `except Exception` handler — meaning they'd get caught and re-wrapped into a more generic message on their way out. Converted to `ExternalServiceError` + an `except ExternalServiceError: raise` guard so their specific, already-safe messages reach the caller intact.

### 2. Fixed — a completely broken endpoint

`DELETE /setting/third-service/{id}` constructed `BaseResponseModel(status="success", ...)`. `BaseResponseModel.status` is typed `int`. Verified empirically: this raises a `pydantic.ValidationError` on every single call, which FastAPI turns into a 500 for the client. **This endpoint could never have succeeded.** mypy had already caught this (`Argument "status" to "BaseResponseModel" has incompatible type "str"`) — flagged in the Phase 1 tooling baseline but not connected to a concrete runtime consequence until traced here. Fixed: `status=200`.

### 3. Verified correct, not changed — object-level authorization

Unlike `url_report` (Domain 2) and pending verification for `url_flag` (Domain 8), **this domain's ownership checks are real and consistently enforced**:
- `ServiceConfService.get_user_services`/`get_service_by_id`/`get_active_services` all filter by `ServiceConf.user_id == user_id` at the query level.
- `ThirdServiceService.get_third_service_by_user` joins through `ServiceConf.user_id == user_id`; `control/third_service_control.py`'s `update()`/`delete()`/`execute()`/`test_execute()` all call this ownership-checked lookup *before* calling the corresponding mutating service method (which themselves don't re-check ownership, but by that point it's already been verified once in the same request).

No IDOR found in this domain. Documented as a positive finding, not left silently unverified.

### Not implemented (confirmed, not assumed) — noted per the master prompt's Feature 6 scope

Priority ordering between multiple active `REST_API` services, retry, and circuit-breaking are **not implemented anywhere in this codebase** — `get_active_services` returns a plain list with no ordering guarantee beyond insertion order, and `_predict_with_third_party` uses whichever single `ServiceConf` was resolved with no fallback/retry logic. Not built in this pass — these are net-new features, not bug fixes, and the master prompt prohibits inventing requirements; if retry/circuit-breaking/priority ordering are wanted, that needs a scoped design decision (thresholds, backoff strategy) this audit can't safely originate from code alone.

## Error-handling sweep

Both routers (`service_conf_route.py`, `third_service_route.py`) were **already clean** — zero `try/except` blocks in either file, confirmed by direct read. No mangled-500 bug existed here; this domain's actual defects were the leak (finding 1) and the broken serialization (finding 2), not the systemic router-catch pattern seen in auth/reports/access-keys.

## Testing

- `tests/unit/test_third_service_executor_errors.py` (new, 3 cases): vendor response body with an embedded secret is not leaked on an HTTP-status error; connection-error text (internal hostname) is not leaked; redirect response is rejected, not followed (`follow_redirects=False` asserted on the client constructor call).
- `tests/unit/test_third_service_route_delete.py` (new, 1 case): `BaseResponseModel(status=200, ...)` for the delete response constructs without error — regression guard for finding 2.

## Migration / rollback

`git checkout -- services/client/third_service_executor.py routers/setting/third_service_route.py tests/unit/test_third_service_executor_errors.py tests/unit/test_third_service_route_delete.py`. No DB/schema impact. `DELETE /setting/third-service/{id}` client-visible change: was unconditionally 500, now correctly returns 200 — a bug fix, not a contract break (no client could have depended on the 500 being "correct" behavior).
