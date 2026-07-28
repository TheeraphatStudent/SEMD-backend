# Indexes

## What exists

No explicit `CREATE INDEX` statements anywhere in `database/semd.db.sql` — confirmed by grep. Every index that exists is implicit: primary keys (auto-indexed by Postgres) and `UNIQUE` constraints (`users.username`, `users.email`, `refresh_tokens.token_hash`, `refresh_tokens.jti`, `activity_log.request_id`, `system_config.config_key`, plus the `UNIQUE` FK columns on `model_registry.service_conf_id` and `third_service_conf.service_conf_id`).

## Query patterns with no index support (evidence, not speculation)

Per the mandate's explicit instruction ("do not add indexes without evidence from query patterns"), these are documented as **candidates evidenced by actual code**, not added:

| Query pattern | Where | Frequency |
|---|---|---|
| `WHERE url_flag.url = ?` (exact match) | `services/url_flag_service.py::check_url_flag`/`check_url_flag_async` | **Every single prediction** — this is the hottest query path in the entire backend, and `url` is an unindexed `Text` column |
| `WHERE user_id = ?` on `access_key`, `prediction`, `url_flag`, `url_report`, `service_conf` | Every domain's "list my own X" endpoint (`get_user_keys`, `get_flags_by_user`, `get_reports_by_user`, `get_user_services`) | Common, one per list-view page load |
| `WHERE access_level = 'GLOBAL'` (cast via `text("access_level::text = 'GLOBAL'")`) on `url_flag` | `check_url_flag_async` | Every prediction, combined with the `url` filter above |
| `WHERE third_service_conf_id / model_registry_id ...` joins | `services/third_service_service.py`, `control/model_registry_control.py` | Moderate — admin-facing management endpoints, not hot-path |

**Recommendation, not applied**: `url_flag.url` (and possibly a composite `(url, access_level)`) is the strongest candidate — it's queried on every single prediction request, unindexed, on a `Text` column. This should be validated against real query-plan data (`EXPLAIN ANALYZE`) once there's production-representative data volume, not added speculatively against an empty/small dev database where the difference wouldn't show up.

## Why nothing was added in this pass

Every domain's changes in this refactor were behavior/security-motivated (authorization fixes, error-handling, SSRF). None of the 13 domains' work required a new query pattern that would justify an index as part of that specific fix — adding one here would be scope creep into performance tuning, which the mandate explicitly gates on evidence this repo doesn't yet have (no query logs, no `pg_stat_statements` data, no production traffic pattern available in this environment).
