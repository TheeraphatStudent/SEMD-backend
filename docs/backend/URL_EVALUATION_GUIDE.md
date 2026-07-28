# URL Evaluation Guide

Full technical detail: `docs/backend/features/url-evaluation/README.md`. This is the consumer-facing summary.

## Two ways to submit a URL for evaluation

- `POST /prediction/predict` — accepts `url` (string or list), `text_file`, or `csv_file` (multipart), optionally `service_id` to pick a specific detection service. Routes through `PredictionControl`, which resolves a default `ML_MODEL`-type service if none specified, and branches to either the internal ML pipeline (via `semd-ml` over Redis) or an admin-configured third-party detector, depending on the resolved service's type.
- `POST /ml/predict` / `POST /ml/predict/batch` — a separate, more direct path into the ML pipeline specifically (bypasses the service-type branching; always ML-model-based).

Both are protected by the same SSRF/URL-safety validator as of this refactor — submitting a URL to either path gets identical safety treatment.

## What gets rejected now (didn't before)

Loopback addresses, private IPv4/IPv6 ranges, link-local addresses, cloud metadata endpoints (`169.254.169.254`, etc.), `localhost` and aliases, non-`http(s)` schemes, embedded credentials (`user:pass@host`), numeric-encoded IP hosts, and hostnames that resolve (via real DNS lookup) to any of the above — with a `422` and a per-URL reason (`code: UNSAFE_URL`). If your integration was relying on any of these being silently forwarded, that's now a documented, intentional breaking change (see the linked feature doc's full before/after table).

## Flags don't override the model — confirmed, not assumed

If you or an admin has set a URL flag (whitelist/blacklist) for a URL, the response includes `is_flag`/`flag_type`/`flag_id` — but **the underlying detector's classification (`is_malicious`, `predict_class`) is never overridden by a flag**. The detector always runs; the flag is informational metadata alongside it, not a short-circuit. If your integration assumed a whitelist flag suppresses a malicious classification, it doesn't — check `is_flag` yourself and apply whatever precedence your application needs client-side.

## Global vs. private flags — who can set what

Only admins can create or edit a `GLOBAL`-access-level flag (one that affects every user's results) — this was a critical authorization gap fixed in this refactor (see `docs/backend/features/url-flags-whitelist/README.md`). Regular users can still create `PRIVATE` flags scoped to themselves.

## Batch limits

No enforced maximum on `url` list length, `text_file`/`csv_file` size, or line count in this backend — not validated at any layer found. If you're submitting very large batches, be aware there's no server-side guard against it today.
