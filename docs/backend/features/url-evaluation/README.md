# Feature: URL Evaluation (Domain 5) — SSRF hardening

Source diagram also kept at `diagrams/request-sequence.mmd`; rendered inline below.

## Request flow

```mermaid
flowchart TD
    A[POST /prediction/predict or /ml/predict] --> B[AuthGuard.get_current_user]
    B --> C[Extract URL list from body/text_file/csv_file]
    C --> D[reject_unsafe_urls: lexical + DNS-resolved-IP check, all URLs concurrently]
    D -- any URL unsafe --> E[422 ValidationError, code=UNSAFE_URL, per-URL reasons]
    D -- all safe --> F{service_id provided?}
    F -- No --> G[Resolve default active ML ServiceConf]
    F -- Yes --> H[Use given service_id]
    G --> I[PredictionService.predict_with_service]
    H --> I
    I --> J{ServiceConf.service_type}
    J -- ML_MODEL --> K[Push job to ml_prediction_queue, poll ml_result:job_id]
    J -- REST_API --> L[ThirdServiceExecutor.execute: admin-configured base_url, follow_redirects=False, size-capped]
    K --> M[Check user URL flag]
    L --> M
    M --> N[Log usage, enqueue retrain candidate]
    N --> O[Return typed response]
```

## Two independent URL-submission entry points (both now protected)

Confirmed by reading both call chains directly — this backend has **two separate paths** that accept user-supplied URLs, not one:

1. `POST /prediction/predict` (multipart: `url` / `text_file` / `csv_file`) → `routers/prediction/prediction_route.py` → `control/prediction_control.py::PredictionControl.predict()` → `services/prediction_service.py` (branches ML-model vs third-party per `ServiceConf.service_type`).
2. `POST /ml/predict` / `POST /ml/predict/batch` → `routers/ml/ml_route.py` → `services/ml_prediction_service.py::MLPredictionService` **directly** — this path does **not** go through `PredictionControl` at all.

A validator wired into only path 1 would leave path 2 fully exploitable. Both now call the same `core.security.reject_unsafe_urls()` before doing anything else (before queueing to `ml_prediction_queue`, before resolving a default service, before touching the DB).

## What this backend does and does not fetch

Neither path fetches URL content directly — both forward the URL **string** to `semd-ml` over Redis, or to an admin-configured third-party detector via `services/client/third_service_executor.py`. This was established in the Phase 1 audit and holds after this pass. Consequently:

- "response-size limits," "excessive redirects," "outbound timeout" (per the master prompt's SSRF test matrix) don't apply to *this* backend's handling of the *submitted* URL — there's no fetch of it here to limit.
- They **do** apply to `third_service_executor.py`'s call to the third-party detector's API, which is a real outbound fetch — hardened in this pass (see below), pulled forward from Domain 6 since it's the one genuine fetch path and was already open in this file.
- Feature-extraction-time fetching (if any) happens inside `semd-ml`, out of this repo's scope — noted, not audited here.

## The validator (`core/security.py`)

Two layers, both applied via `reject_unsafe_urls()`:

1. **Lexical** (`check_url_safety()`, no network call): scheme allow-list (`http`/`https` only), reject embedded credentials (`user:pass@host`), reject literal loopback/private/link-local/reserved/multicast/CGNAT (100.64.0.0/10) IPv4 and IPv6 hosts, reject known metadata-endpoint hostnames/IPs (`169.254.169.254`, `metadata.google.internal`, `fd00:ec2::254`), reject numeric-encoded hosts (decimal/octal/hex forms of an IP, e.g. `http://2130706433/` for `127.0.0.1`).
2. **DNS-resolution** (`check_url_safety_async()` / `resolve_and_check_dns()`): for any host that isn't a literal IP, resolves it and checks *every* returned address against the same blocklist — this is what actually closes the DNS-rebinding gap (a hostname that only resolves to a private/metadata address at lookup time, which the lexical check alone cannot see). Resolution failure or timeout (3s) is treated as **blocked**, not allowed-through — an unresolvable host can't be legitimately evaluated downstream either.

`reject_unsafe_urls(urls: list[str])` runs both layers concurrently across the whole batch and raises `core.exceptions.ValidationError` (422, `code=UNSAFE_URL`) with a per-URL `{url, reason}` list if any fail — the whole request is rejected, not silently filtered, since there's no existing partial-success contract to build on without inventing one.

## Before / after accepted inputs — documented intentional breaking change

| Input | Before | After |
|---|---|---|
| `https://example.com` | Accepted | Accepted |
| `http://127.0.0.1/admin` | **Accepted** (forwarded to ML queue as-is) | **Rejected**, 422 `UNSAFE_URL` |
| `http://169.254.169.254/latest/meta-data/` | **Accepted** | **Rejected** |
| `http://10.0.0.5/`, `http://192.168.1.1/`, `http://172.16.0.1/` | **Accepted** | **Rejected** |
| `http://localhost/` | **Accepted** | **Rejected** |
| `javascript:alert(1)`, `file:///etc/passwd`, `data:text/html,x` | **Accepted** (forwarded as a string to the queue) | **Rejected** |
| `http://user:pass@example.com/` | **Accepted** | **Rejected** |
| `http://2130706433/` (decimal-encoded 127.0.0.1) | **Accepted** | **Rejected** |
| A hostname that resolves to a private IP (DNS rebinding) | **Accepted** | **Rejected** |
| An unresolvable hostname | Accepted (would fail downstream in `semd-ml` anyway) | **Rejected** upfront, with a clear reason instead of a silent downstream failure |

This is a deliberate, documented breaking change for the rejected rows above — not accidental. No settings-flag gate was added (the roadmap's Phase 3 draft suggested one); given the fix closes a real, currently-exploitable SSRF/injection gap and the rejected input classes have no legitimate use case in a malicious-URL-detection product, shipping it directly (rather than flagged-off) was judged the correct call. If real traffic depends on any of these being accepted, that would surface immediately as a spike in `UNSAFE_URL` 422s — recommend watching that in the first deployment.

## `third_service_executor.py` hardening (pulled forward from Domain 6)

The one path in this backend that performs a real outbound fetch (to an admin-configured third-party detector's API, e.g. Cloudflare Radar, Thai PhishTank):

- `follow_redirects=False` made **explicit** on the `httpx.AsyncClient` (was relying on httpx's own default, which is also `False` — behavior unchanged, but a security property should not depend silently on a library default that could change). A redirect response is now explicitly rejected (502) rather than silently returned as an unfollowed redirect body.
- Response-size guard: rejects (502) if `Content-Length` declares more than 5 MiB, and rejects post-fetch if the buffered body exceeds it. **Documented limitation**: this is not a true streaming cap — `httpx`'s non-streaming `client.request()` already buffers the full response before either check runs, so a server that lies about `Content-Length` and sends an enormous body without one is not protected against memory exhaustion by this change. A true fix requires rewriting this call to use `client.stream()` with an early-abort on byte count — not done in this pass (larger diff, and `base_url` here is admin-configured, not attacker-controlled, which lowers the priority relative to the SSRF fix above).
- Removed a stray `print(e)` debug statement (replaced with `logger.warning(..., exc_info=e)`).

Not touched (left for Domain 6, which owns this file's remaining error-handling sweep): the `except httpx.RequestError`/`except Exception` blocks still put `str(e)` into `detail`, which may be appropriate for the admin-facing "test connection" endpoint but not for other callers — needs the caller-context analysis Domain 6 is scoped to do.

## Testing

- `tests/unit/test_core_security.py` (pre-existing from Phase 3) — 13 lexical cases.
- `tests/unit/test_core_security_dns.py` (new) — 5 cases, DNS mocked (no live network dependency): private-IP resolution blocked, public-IP resolution allowed, resolution failure blocked, DNS-rebinding case end-to-end through `check_url_safety_async`, literal-IP path skips DNS entirely.
- `tests/unit/test_prediction_ssrf.py` (new) — 5 cases proving the wiring, not just the validator: `PredictionControl.predict()` rejects loopback/metadata URLs *before* calling `prediction_service.predict_with_service` (mocked and asserted not-called), allows a public literal IP through; `MLPredictionService.predict_url`/`predict_urls` reject private IPs *before* calling `ml_service_client` (asserted not-called), and a batch request reports exactly which URL(s) were rejected.

**Known test-suite caveat**: `tests/unit/test_ml_prediction_service.py` (pre-existing) and `test_prediction_ssrf.py`'s dispatch-through test use `example.com`/a literal public IP — the `example.com` case now triggers a real DNS lookup as part of the full call path. Verified fast (<100ms) in this environment. If this suite ever runs in a network-isolated CI runner, that test would need `resolve_and_check_dns` mocked the way `test_core_security_dns.py` already does it.

## Migration / rollback

Files: `core/security.py` (extended), `control/prediction_control.py`, `services/ml_prediction_service.py`, `services/client/third_service_executor.py`. Rollback: `git checkout -- core/security.py control/prediction_control.py services/ml_prediction_service.py services/client/third_service_executor.py tests/unit/test_core_security_dns.py tests/unit/test_prediction_ssrf.py` — reverts to the Phase-3 state where the validator existed but wasn't called anywhere (fully inert, zero risk).

## Deferred, not part of this pass

- File-upload validation for `text_file`/`csv_file` in `/prediction/predict` (size limits, content-type checks) — flagged in Phase 1, not re-verified or fixed here; separate finding from SSRF.
- Rate limiting on prediction endpoints — no rate-limiting infrastructure exists anywhere in this backend yet (cross-cutting Phase 3 gap, not domain-specific).
- Streaming-based true response-size cap for `third_service_executor.py` (see above).
