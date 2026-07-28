# Table Dictionary

All 13 tables in `database/models.py`, as of the Phase 3 `ForeignKey()` additions. `Enum(...)` = real Postgres native enum column; plain `String` = app-level-only validation against `libs/types/enums.py`.

## `users`

| Column | Type | Nullable | Default | Constraint | Description |
|---|---|---|---|---|---|
| user_id | BigInteger | No | autoincrement | PK | |
| username | String(32) | No | — | UNIQUE | |
| email | String(64) | No | — | UNIQUE | |
| full_name | String(512) | No | — | | |
| birthday | TIMESTAMP(tz) | Yes | — | | |
| password_hash | String(1024) | No | — | | bcrypt hash |
| role | String(20) | No | `MEMBER` | | app-level only — `RoleType`; not a DB enum |
| gg_id, gg_acc_token, gg_re_token | Text | Yes | — | | Google OAuth linkage + live tokens |
| gh_id, gh_acc_token, gh_re_token | Text | Yes | — | | GitHub OAuth linkage + live tokens |
| twofa_secret | Text | Yes | — | | **plaintext at rest** — open finding, see `standards/SECURITY.md` |
| is_2fa_enabled | Boolean | No | `false` | | |
| ex_acc_token | Text | Yes | — | | extension access token, **hashed (sha256) as of Domain 4** |
| ex_acc_token_exp | TIMESTAMP(tz) | Yes | — | | |
| profile_img_uri | Text | Yes | — | | |
| created_at, updated_at | TIMESTAMP(tz) | No | `now()` | | |

## `refresh_tokens`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| refresh_tokens_id | BigInteger | No | PK |
| user_id | BigInteger | No | FK → users.user_id, `ON DELETE CASCADE` |
| token_hash | String(64) | No | UNIQUE — sha256 of the JWT |
| jti | UUID | No | UNIQUE |
| expires_at | TIMESTAMP(tz) | No | |
| is_revoked | Boolean | No, default `false` | |
| created_at | TIMESTAMP(tz) | No | |

## `service_conf`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| service_conf_id | BigInteger | No | PK |
| user_id | BigInteger | Yes | FK → users.user_id, `ON DELETE CASCADE` |
| service_name | String(32) | No | |
| service_type | **Enum**('REST_API','ML_MODEL') | No | real Postgres enum |
| is_active | Boolean | No, default `true` | |
| version_no | String(12) | No | |
| config_uri | Text | No | |
| config_json | JSON | No, default `{}` | |
| created_at, updated_at | TIMESTAMP(tz) | No | |

## `model_registry`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| model_registry_id | BigInteger | No | PK |
| service_conf_id | BigInteger | Yes | UNIQUE, FK → service_conf, `ON DELETE CASCADE` |
| name, algorithm | String(64) | No | |
| mlflow_run_id | String(64) | No | |
| mlflow_model_version | Integer | Yes | |
| experiment_id | String(64) | Yes | |
| stage | String(20) | No, default `NONE` | app-level only — `ModelStageType` |
| model_uri, scaler_uri, label_uri, selecter_uri | Text | No | **Domain 10 finding**: previously settable by any MEMBER; now admin-gated |
| accuracy_score, recall_score, precision_score, f1_score | Numeric(5,4) | Yes | |
| description | Text | Yes | |
| tags | JSON | No, default `{}` | |
| created_at, updated_at | TIMESTAMP(tz) | No | |

## `access_key`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| access_key_id | BigInteger | No | PK |
| user_id | BigInteger | Yes | FK → users.user_id, `ON DELETE CASCADE` |
| key_name | String(64) | Yes | |
| access_key_hash | Text | No | sha256, raw key shown once — correct pattern, confirmed Domain 3 |
| is_active | Boolean | No, default `true` | |
| usage_limit | BigInteger | Yes | |
| expired_at | TIMESTAMP(tz) | No | |
| created_at, updated_at | TIMESTAMP(tz) | No | |

## `prediction`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| prediction_id | BigInteger | No | PK |
| user_id | BigInteger | Yes | FK → users.user_id, `ON DELETE SET NULL` |
| url | Text | No | |
| accuracy_score, recall_score, precision_score, f1_score | Numeric(10,2) | Yes | |
| is_malicious | Boolean | No | |
| predict_class | String(64) | No | |
| suggested_desc | String(512) | Yes | |
| created_at | TIMESTAMP(tz) | No | |

## `url_flag`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| url_flag_id | BigInteger | No | PK |
| user_id | BigInteger | Yes | FK → users.user_id, `ON DELETE CASCADE` |
| url | Text | No | queried by exact match on every prediction (`check_url_flag`) — see `indexes.md` |
| type | String(20) | No, default `BENIGN` | app-level only — `FlagType` |
| access_level | String(20) | No, default `PRIVATE` | app-level only — `ACLType`. **Domain 8 finding**: `GLOBAL` value previously settable by any MEMBER; now admin-gated |
| created_at, updated_at | TIMESTAMP(tz) | No | |

## `url_report`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| url_report_id | BigInteger | No | PK |
| user_id | BigInteger | Yes | FK → users.user_id, `ON DELETE CASCADE` |
| url | Text | No | |
| categories | String(20) | No, default `BENIGN` | app-level only — `FlagType` |
| status | String(20) | No, default `PENDING` | app-level only — `ReportStatusType` (3 states: PENDING/ACCEPTED/REJECTED). **Domain 2 finding**: previously editable by any authenticated user regardless of ownership; now ownership + admin-status-change enforced |
| remark | String(256) | Yes | |
| created_at, updated_at | TIMESTAMP(tz) | No | |

## `activity_log`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| activity_log_id | BigInteger | No | PK |
| user_id | BigInteger | Yes | FK → users.user_id, `ON DELETE SET NULL` |
| method | String(16) | No | |
| endpoint | String(1024) | No | |
| request_id | String(32) | No | UNIQUE |
| client_ip | String(32) | Yes | |
| client_agent | String(256) | Yes | |
| response | String(512) | Yes | |
| created_at, updated_at | TIMESTAMP(tz) | No | |

**This table is never written to anywhere in the codebase** — confirmed by repo-wide grep during Domain 13. Schema-only, unused. See `docs/backend/features/system-audit-logs/README.md`.

## `usage_log`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| usage_log_id | BigInteger | No | PK |
| service_id | BigInteger | Yes | FK → service_conf, `ON DELETE SET NULL` |
| access_key_id | BigInteger | Yes | FK → access_key, `ON DELETE SET NULL` |
| prediction_id | BigInteger | Yes | FK → prediction, `ON DELETE SET NULL` |
| type | **Enum**('PREDICT','ACCESS_KEY') | No | real Postgres enum |
| created_at | TIMESTAMP(tz) | No | |

Actually populated (unlike `activity_log`) — via `services/usage_log_service.py`, called from `control/prediction_control.py` on every prediction.

## `third_service_conf`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| third_service_conf_id | BigInteger | No | PK |
| service_conf_id | BigInteger | Yes | UNIQUE, FK → service_conf, `ON DELETE CASCADE` |
| service_name | String(64) | No | |
| base_url | Text | No | admin-configured; not user-controlled (confirmed Domain 5/6 — lowers SSRF risk on this table specifically) |
| http_method | String(8) | No, default `GET` | |
| headers_json, config_json, mapping_json | JSON | No, default `{}` | |
| is_active | Boolean | No, default `true` | |
| created_at, updated_at | TIMESTAMP(tz) | No | |

## `url_reported`

Audit-history table for `url_report` status transitions — the one genuine per-domain audit trail in the whole schema (see `standards/SECURITY.md`/Domain 13).

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| url_reported_id | BigInteger | No | PK |
| url_report_id | BigInteger | No | FK → url_report, `ON DELETE CASCADE` |
| user_id | BigInteger | No | FK → users.user_id, `ON DELETE SET NULL` — **DDL contradiction**: `semd.db.sql` declares this both `NOT NULL` and `ON DELETE SET NULL`; deleting a referenced user would violate the `NOT NULL` constraint. Matched as-is in the ORM to reflect current DB behavior; not resolved (see `README.md`) |
| action | String(32) | No | e.g. `CREATE`, `UPDATE`, `STATUS_CHANGE` |
| old_status, new_status | String(20) | Yes | |
| remark | String(256) | Yes | |
| created_at | TIMESTAMP(tz) | No | |

## `system_config`

| Column | Type | Nullable | Constraint |
|---|---|---|---|
| system_config_id | BigInteger | No | PK |
| config_key | String(64) | No | UNIQUE |
| config_value | Text | No | |
| description | String(256) | Yes | |
| created_at, updated_at | TIMESTAMP(tz) | No | |
