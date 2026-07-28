# Observability Standard

## Structured logging (built, Phase 3)

`core/logging.py::configure_logging()` — one JSON line per log record via a custom `JsonFormatter`, called from `application.py::create_application()` with level `DEBUG` if `settings.debug` else `INFO`. Every record includes `timestamp`, `level`, `logger`, `message`, plus any `extra={}` fields passed at the call site.

## Request correlation (built, Phase 3)

`core/middleware.py::RequestContextMiddleware` — generates a request ID (or passes through an inbound `X-Request-ID` header), stores it on `request.state.request_id`, echoes it as the `X-Request-ID` response header, and emits one structured access-log line per request:

```json
{"level": "INFO", "logger": "semd.access", "message": "request completed",
 "request_id": "...", "method": "GET", "path": "/prediction/predict",
 "status_code": 200, "duration_ms": 42.1}
```

Deliberately excludes query string and headers from the access log (a URL's query params could carry tokens/PII; see "never log" list below).

## Error logging (built, Phase 3)

`core/error_handlers.py::handle_unexpected_error` logs every unhandled exception server-side with `exc_info` (full traceback) and the request ID, before returning a generic message to the client — this is the mechanism that makes the "no `str(e)` leak" fix (Domains 1-13) safe without losing debuggability; the real error is always in the logs, correlated by request ID.

## What is NOT built (confirmed gaps, not silently assumed complete)

| Requirement (from the master prompt) | Status |
|---|---|
| Request duration | **Done** — `duration_ms` on every access-log line |
| Error counts / auth-failure counts | **Not built** — no metrics aggregation exists; would need to be derived from log volume (e.g. a log-based metric in whatever platform ingests these JSON lines) or a dedicated counter (Prometheus client, StatsD) not currently wired in |
| URL-evaluation / detector latency | **Partially available** — `MLPredictResponse.prediction_time_ms` is returned in the API response (sourced from `semd-ml`'s own reported timing), but not separately logged/aggregated on this side |
| Database / Redis latency | **Not built** — no query-timing instrumentation exists |
| Model-loading status | N/A to this backend — no model is ever loaded here (confirmed Phase 1) |
| Training-job status | Available via polling (`GET /ml/training/result`), not pushed/logged as a metric |
| Detector failure rate | **Not built** — individual failures are logged (Domain 6's `logger.warning` on connection/status errors), but no aggregated rate |

Building real metrics (Prometheus, OpenTelemetry, or a hosted APM) is a genuine infrastructure decision (which system, which deployment target) not made in this codebase — flagged as future work, not fabricated here.

## Never log (verified against, not just stated)

Passwords, JWTs, refresh tokens, TOTP secrets, OAuth tokens, full API keys, full Access Codes, sensitive personal data, private dataset contents. Verified in practice: the access-log middleware logs only method/path/status/duration (no body, no headers, no query string); the error handler logs the exception object via `exc_info`, which could theoretically include a secret if a secret were embedded in an exception *message* by application code — none of the exception-raising code audited across Domains 1-13 embeds secrets in messages (the opposite finding — `str(e)` leaking to the *client* — was the actual bug, now fixed; server-side logging of the same `exc_info` was always intended and is correct).

## Health endpoints (built, Phase 3)

`GET /health/live` — process is up, no dependency calls. `GET /health/ready` — checks Postgres and Redis reachability with a 3s timeout each, returns `503` if either is down. Does not depend on optional third-party detectors (per the mandate's rule that readiness shouldn't fail on non-mandatory dependencies). The pre-existing `GET /health` (no `/live`/`/ready` suffix) still returns hardcoded fake CPU/memory/disk figures — left as a deprecated-in-practice alias, not removed (see `SEMD_BACKEND_CURRENT_STATE.md` section 2), since removing a live endpoint wasn't in scope for any single domain's charter.
