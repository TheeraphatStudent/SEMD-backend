# Advisor Feedback Remediation (2026-07)

Response to a batch of thesis-advisor comments covering dataset provenance, model
justification, feature documentation, evaluation metrics, browser-extension login,
and four schema changes. Every claim below is cited to a file in this repo (or the
`semd-ml` sibling repo) as of this pass. Where the advisor's comment asked for
something this repo cannot supply on its own (a citation, a real dataset count, a
thesis table's own numbering) it is scaffolded here and listed in **NEEDS AUTHOR
INPUT** at the end rather than invented.

## 1. Step 0 — what already existed (scan report)

This backend has already been through a prior security/permissions audit (its own
"Domain 1–13" pass, documented under `docs/backend/features/*/README.md`). Several
items in the advisor's list turned out to already be implemented as a result of that
audit, not gaps. Read before writing anything:

- `models/db/entities.py` — all 13 SQLAlchemy tables, one file.
- `docs/backend/database/table-dictionary.md` — full column-by-column dictionary,
  already current with this pass's changes.
- `docs/backend/database/migration-guide.md` — this project has **no Alembic**;
  `docker/postgres/init.sql` is raw DDL that only runs on a fresh Postgres data
  directory. Schema changes to a live database are applied by hand — see
  `docker/postgres/migrations/0001_oauth_cleanup_and_report_review.sql` (new,
  added in this pass).
- `libs/types/enums.py` — shared enums (`RoleType`, `FlagType`, `ACLType`,
  `ReportStatusType`, `OAuthProviderType`, etc.)
- `docs/backend/features/url-flags-whitelist/README.md`,
  `docs/backend/features/url-reports/README.md`,
  `docs/backend/features/extension-access-codes/README.md` — prior audit findings
  directly relevant to items 5 and the extension note below.
- `guard/auth_guard.py` — `AuthGuard`, FastAPI auth dependencies.
- `control/prediction_control.py`, `services/url_flag_service.py`,
  `services/queue_service.py` — already accept `user_id=None` / `user=None`
  end-to-end (anonymous prediction was already half-built before this pass).
- `semd-ml/src/features/features.yaml` + `semd-ml/src/features/extractor.py` — the
  real feature list and its implementation.
- `semd-ml/src/data/data_dict.yaml` + `semd-ml/src/dataset/raw/*.csv` — real dataset
  sources and label-mapping config.

The root `CLAUDE.md`'s description of this backend is stale in two places: it says
the ORM lives at `database/models.py` (actually `models/db/entities.py`) and that
"no test suite exists" (actually `tests/unit/`, 86 tests, run via
`python -m unittest discover -s tests/unit`). Status summary below is grounded in
the code, not that file.

## 2. Task 1 — Project status summary

**Backend (semd-backend).** Layered `routers/ → control/ → services/ → models/db/`
FastAPI app. Auth supports Bearer-token sessions, `x-api-key` API keys, Google OAuth
(GitHub OAuth removed in this pass, see item 5). Role model is
`GUEST/MEMBER/ADMIN/SUPER_ADMIN`. 13 tables covering users, refresh tokens, ML
service/model registry, access keys, predictions, URL flags (blacklist/whitelist),
URL reports + their audit trail, activity/usage logs, third-party service config,
system config. A prior internal audit (Domains 1–13) already fixed several
authorization gaps — IDOR on report status changes, unrestricted GLOBAL-flag
creation, secret fields leaking through `UserModel`. `tests/unit/` has 86 passing
tests.

**ML (semd-ml).** Classical-ML pipeline (SVM, Decision Tree, Random Forest,
XGBoost) over 73 hand-engineered lexical/structural URL features (no WHOIS/DNS/live
lookups — see item 3). Real raw data sources are present on disk with real row
counts (see item 1), but the dataset artifact the pipeline last actually produced
(`dataset/raw/merged.csv`) was built from a 20-row synthetic smoke-test fixture, not
the real sources — see item 1 for the exact state.

**Frontend / extension.** Not modified in this pass beyond the one client-side fix
in item 4 (extension no longer hard-blocks calling predict without an Access Code).
Root `CLAUDE.md` describes the rest of both modules' structure; not re-derived here.

**Stubbed / incomplete, confirmed by this pass:**
- Extension access-code exchange flow (`docs/backend/features/extension-access-codes/README.md`):
  generation-only before this pass; still no `/validate` exchange endpoint — item 4's
  fix is a separate, narrower thing (anonymous predict), not that flow.
- `activity_log` table: schema exists, nothing in the codebase writes to it
  (`table-dictionary.md:131`).
- Dataset-queue eligibility (report acceptance → retrain queue): does not exist;
  the retrain queue is pushed on every prediction, unconditionally
  (`docs/backend/features/url-reports/README.md:26-28`).
- Neither `url_flag` nor `url_report` overrides the ML/third-party detector's
  verdict — both are informational/audit only (see item 4, "Data Flow").

## 3. Remediation table

| # | Item | CODE / DOC | Status | Acceptance criteria met? |
|---|---|---|---|---|
| 1 | Data Set sourcing, counts, real-vs-mock | DOC | Scaffolded, real counts computed where possible | Partial — counts real where computable; author input needed for citations/credibility narrative |
| 2 | Model justification (SVM/DT/RF/XGB) + lit review | DOC | Scaffolded with citation slots | No — citations cannot be invented |
| 3 | Feature list, justification, extractability | DOC + CODE | Feature list pulled from real code; extractability diff done | Yes (code part); citations need author |
| 4a | Metrics rationale (F1/Recall/Precision/Accuracy/FNR/FPR) | DOC | Written | Yes |
| 4b | Extension: no login + graceful expiry | CODE | Implemented | Yes |
| 4c | Data Flow description | DOC | Written | Yes |
| 5a | Drop nullable-annotation notes in data dictionary | DOC | Reviewed; dictionary already didn't restate nullability as prose | Yes (already compliant) |
| 5b | `username` UNIQUE | CODE | Already present | Yes |
| 5c | `email` UNIQUE | CODE | Already present | Yes |
| 5d | Drop user fields 10/11 | CODE | Implemented (`gg_re_token`, `gh_id` dropped; GitHub OAuth retired) | Yes |
| 5e | Table 3.24 — blacklist/whitelist shared+private+authority | CODE + DOC | Already present (`url_flag.access_level` GLOBAL/PRIVATE, admin-gated) | Yes |
| 5f | Table 3.25 — report approved/disapproved + reviewer + timestamp | CODE + DOC | Status already present; `reviewed_by`/`reviewed_at` added this pass | Yes |
| 5g | Web + API plugin usable without session | CODE | Implemented (same fix as 4b) | Yes |

## 4. Code changes made, in reasoning order

### 4b/5g — Extension: anonymous access to `/prediction/predict`

**Domain modeling.** A caller identity for this endpoint is now optional, not
required. Business logic already modeled this (`PredictionControl.__init__`'s
`user_id: int = None` default, `UrlFlagService.check_url_flag(_async)`'s
`Optional[int]` branch, `QueueService.add_to_retrain_queue`'s `Optional[User]`) —
confirmed by reading each before writing the guard, per the advisor's own note that
this was probably the actual remaining gap.

**Schema.** No schema change — `Prediction.user_id` was already
`nullable=True, ondelete='SET NULL'`.

**Logic.** New dependency `guard/auth_guard.py::_get_current_user_optional`
(exposed as `AuthGuard.get_current_user_optional`): parses `Authorization: Bearer`
if present; returns `None` — never raises — on a missing header, malformed header,
or an expired/invalid/unknown-user token.

**Code.**
- `guard/auth_guard.py` — added `_get_current_user_optional` and the `AuthGuard`
  class attribute.
- `routers/prediction/prediction_route.py::predict` — dependency changed from
  `AuthGuard.get_current_user` (hard 401) to `AuthGuard.get_current_user_optional`;
  `current_user` is now `Optional[User]`; `user_id` passed to `PredictionControl` is
  `None` when there's no valid caller.
- `semd-extension/src/extension/shared/api.ts::evaluateUrlWithApi` — removed the
  client-side `if (!settings.accessCode) return "missing_access_code"` hard block
  (this was gating the call *before* it ever reached the backend, independent of
  anything the backend could fix). `x-api-key` is now sent only when an Access Code
  is configured.

Chose **fully anonymous, optional credential** over the `x-api-key`-only option
(both were offered; anonymous was selected) — matches the extension's existing
behavior of sending a bare `x-api-key` today with the header simply not validated
on this route.

### 5d — Drop `users.gg_re_token` and `users.gh_id`; retire GitHub OAuth login

**Domain modeling.** Two candidate field-10/11 numberings existed in this repo
(declaration order in `entities.py` vs. `table-dictionary.md`'s row order); neither
matched an in-repo thesis table (grep for "3.24"/"3.25" across the whole project
found nothing outside `.agents/skills/` reference docs). The project owner selected
declaration order (`gg_re_token`, `gh_id`) when asked directly during this
implementation pass, and confirmed that Google remains the only login provider —
GitHub OAuth is being retired. (Unlike the file citations elsewhere in this
document, that is an interactive session decision, not something verifiable from
repo history — re-confirm it before treating it as settled.)

**Schema.**
- `models/db/entities.py::User` — `gg_re_token` and `gh_id` columns removed.
- `docker/postgres/init.sql` — same two columns removed from the `users` DDL (fresh
  installs).
- `docker/postgres/migrations/0001_oauth_cleanup_and_report_review.sql` — new file,
  `ALTER TABLE users DROP COLUMN` for both, to be run by hand against any
  already-running database (see migration-guide.md addendum, § "no Alembic").

**Logic.**
- `libs/types/enums.py::OAuthProviderType` — `GITHUB` removed; `GOOGLE` is the only
  value. This is the single gate: any client request specifying
  `provider: "github"` now fails FastAPI/Pydantic request validation before
  reaching any handler.
- `services/oauth_service.py::upsert_oauth_user` — the three `if provider ==
  'github': ... gh_id ...` branches removed (would otherwise raise `AttributeError`
  the moment a GitHub-flow caller reached this function, now unreachable anyway via
  the enum gate, but removed for defense in depth).
- `models/auth/user_model.py::UserModel` — `gh_id` field removed (Pydantic response
  schema mirrors the dropped column); docstring updated.

**Verified before touching anything:** grepped `gg_re_token` and `gh_id` across
`semd-backend`, `semd-frontend`, `semd-extension`. `gg_re_token` — zero reads/writes
anywhere outside the column declaration and a docstring/test listing it as an
excluded secret field (confirmed dead). `gh_id` — actively read/written in
`services/oauth_service.py:281,296,321` for GitHub-account lookup/linking; this is
why the enum change (not just the column drop) was necessary to avoid shipping a
crash.

**Left alone, flagged, not in scope for this pass:** `gh_acc_token`/`gh_re_token`
columns still exist on `users` — now orphaned (their linking key, `gh_id`, is gone)
but not dropped, since only fields 10/11 were confirmed in scope. The low-level
GitHub HTTP helpers in `services/oauth_service.py`
(`initiate_github_device_flow`, `poll_github_device_flow`,
`generate_github_authorization_url`, `exchange_github_code`,
`get_github_user_info`, `exchange_github_token`) and the per-provider `if
request.provider.value == 'github'` branches in `control/auth_control.py` are now
unreachable via the API (the enum blocks it) but were not deleted — removing an
entire OAuth device-flow code path is a larger, separate cleanup from a two-column
schema drop and wasn't requested. Recommended as a followup once GitHub OAuth
retirement is confirmed as final.

**Tests:** `tests/unit/test_user_model_no_secrets.py` updated (`gh_id` removed from
the "kept field" assertions and the fake ORM object); full suite (86 tests) passes.

### 5f — `url_report.reviewed_by` / `reviewed_at`

**Domain modeling.** Table 3.25's "human over AI" requirement is largely already
implemented: `ReportStatusType` (`PENDING`/`ACCEPTED`/`REJECTED`,
`libs/types/enums.py:17-20`) with admin-only status transitions
(`services/url_report_service.py::update_report`), and every transition already
logged to `url_reported` (who: `user_id`, when: `created_at`, what:
`old_status`/`new_status`) per `docs/backend/features/url-reports/README.md`. The
open gap was that "who reviewed this, and when" required a join to the audit table
instead of being a direct column on the report itself. The project owner chose to
add the direct columns (vs. "the audit table is enough") when asked directly during
this implementation pass — an interactive session decision, not a claim verifiable
from repo history like the file citations elsewhere in this document.

**Schema.**
- `models/db/entities.py::UrlReport` — `reviewed_by` (`BigInteger`, FK →
  `users.user_id`, `ON DELETE SET NULL`, nullable) and `reviewed_at`
  (`TIMESTAMP(tz)`, nullable) added.
- `docker/postgres/init.sql` and the new
  `docker/postgres/migrations/0001_oauth_cleanup_and_report_review.sql` — both
  columns added (additive, nullable — existing rows unaffected).
- `models/report/url_report_model.py::UrlReportModel` — both fields added to the
  response schema.

**Logic.** `services/url_report_service.py::update_report` — when an admin changes
`status` (already the only path that can change it), `reviewed_by`/`reviewed_at`
are set alongside it. `models/report/url_report_request.py::UrlReportUpdateRequest`
was deliberately **not** given these fields — they're server-derived from the
authenticated admin, not client-settable.

**What still isn't true, and is flagged rather than silently fixed:** neither
`url_flag` nor `url_report` overrides the underlying ML/third-party verdict — see
"Data Flow" below. A human can record a decision; it doesn't change what
`is_malicious`/`predict_class` the detector returns for that URL on the next call.
Whether that's the intended design (flags/reports are audit annotations only,
enforcement happens elsewhere or hasn't been built) or a real gap is a product
decision, already flagged in `docs/backend/features/url-flags-whitelist/README.md:30`
and not something this pass invented a resolution for.

### 4c — Data Flow

```
client (web / extension, no login required)
  -> POST /prediction/predict
  -> PredictionControl.predict()
       -> PredictionService.predict_with_service()
            branches on ServiceConf.service_type:
              ML_MODEL  -> ml_service_client -> Redis "ml_prediction_queue"
                           -> semd-ml worker (queue_worker.py -> prediction_service.py
                              -> feature_extractor.extract(), 73 lexical/structural
                              features, no live network lookups)
                           -> Redis "ml_result:{job_id}" -> polled back
              REST_API  -> ThirdServiceExecutor -> configured third-party
                           (Cloudflare Radar, Thai PhishTank, etc. via
                           POST /setting/third-service registration)
       -> usage_log_service.log_prediction_usage() (persisted)
       -> _check_url_flag() (UrlFlagService, GLOBAL-or-owned lookup) -- annotation
          only, does not change is_malicious/predict_class
       -> QueueService.add_to_retrain_queue() -- every prediction, unconditionally
  -> response: is_malicious, predict_class, is_flag/flag_type (if any), scores
```

Separately, a **logged-in** user may also `POST /report/` a URL
(`UrlReportControl.create_report`) independent of the predict call. Only
`/prediction/predict` was made anonymous-capable in this pass; `/report/` still
requires a Bearer token (`routers/report/report_route.py` —
`Depends(AuthGuard.get_current_user)`, untouched here) and
`UrlReportService.create_report` reads `user_id=user.user_id`, so an anonymous
caller could not reach it even if the dependency were relaxed. An admin later
reviews it (`update_report`) — see item 5f. This review path does not feed back
into the predict path above (see the "not overridden" note in 5f).

## 5. NEEDS AUTHOR INPUT

Everything below requires facts this repo cannot supply. Do not fill from memory —
mark anything still unknown as `PLACEHOLDER`.

### Item 1 — Data Set

**What's real vs. mock, confirmed from files (not guessed):**

| File | Rows | Status |
|---|---|---|
| `dataset/raw/merged.csv` (the artifact `data-migrate` most recently produced) | 20 | **Mock** — `merged.metadata.json` shows it was built from `t093_smoke_fixture.csv` alone, a synthetic smoke-test fixture (`benign0.example.com`, `benign1.example.com`, ...) |
| `dataset/raw/malicious_url_train2.csv` | 481,835 (label col) | Real; label counts computed below |
| `dataset/raw/malicious_url_test2.csv` | 25,360 | Real; label counts computed below |
| `dataset/raw/url_spam_classification.csv` | 148,303 | Real; label counts computed below |
| `dataset/raw/cloudflare_malicious_scans_20260307_185943.csv` | 1,300 | Real, single-source Cloudflare Radar export; all rows `label=malicious` |
| `dataset/raw/phishtank-verified_online.csv` | 56,259 | Real PhishTank export; single-class feed (every row is a verified phish), no benign rows in this file by design |
| `dataset/raw/url-hasus.csv` | 77,358 | Real URLhaus export; single-class feed (malware URLs only), no benign rows in this file by design |
| `dataset/raw/HiddenFraudulentURLs.csv` | 185,180 | Real file present, but **not usable as-is**: semicolon-delimited, columns (`compromissionType`, `isHiddenFraudulent`, ...) don't match any name in `data/data_dict.yaml`'s `fields.url`/`fields.class` lists — the migration pipeline cannot currently ingest this file without either a data_dict.yaml update or a preprocessing step |
| `dataset/raw/dataset_with_all_features v2.csv` | ~unknown, not counted | Appears to be a pre-computed feature output, not a raw label source |
| `dataset/raw/dataset.example.csv` | 0 (header only) | Placeholder, not a data source |

**Counts computed directly from the files** (using `data_dict.yaml`'s
`class_mapping`, benign/malicious only, no report-time sampling):

| Source | Benign | Malicious | Total |
|---|---|---|---|
| `malicious_url_train2.csv` | 373,252 | 108,583 | 481,835 |
| `malicious_url_test2.csv` | 19,645 | 5,715 | 25,360 |
| `url_spam_classification.csv` | 101,021 | 47,282 | 148,303 |
| `cloudflare_malicious_scans_20260307_185943.csv` | 0 | 1,300 | 1,300 |
| `phishtank-verified_online.csv` | 0 (not applicable — single-class feed) | 56,259 | 56,259 |
| `url-hasus.csv` | 0 (not applicable — single-class feed) | 77,358 | 77,358 |

**Known config gap, found while computing the above:**
`data/dataset_group` in `data_dict.yaml` lists filenames that don't match what's
actually on disk — `urlhasus.csv` vs. the real `url-hasus.csv`; `huggingface:
malicious_urls_test2.csv/malicious_urls_train2.csv` (plural "urls") vs. the real
`kaggle: malicious_url_test2.csv/malicious_url_train2.csv` (singular). Whether this
is a stale config or the pipeline resolves it another way wasn't traced further —
flagged rather than assumed.

**Author must supply, since this repo cannot:**
- Source credibility citation for each of PhishTank, URLhaus, Cloudflare Radar,
  the Kaggle malicious-URL datasets, and the spam-classification dataset —
  `[CITATION NEEDED: <source name>]`.
- Whether `HiddenFraudulentURLs.csv` is intended to be wired in (needs a
  `data_dict.yaml` fix) or dropped from the source list.
- The actual merged, deduplicated, final train/test counts once `data-migrate` is
  re-run against the real sources instead of the smoke fixture — the numbers above
  are per-source, pre-merge, pre-dedup, pre-balancing.

### Item 2 — Model justification (SVM / Decision Tree / Random Forest / XGBoost)

Each needs a justification paragraph framed around malicious/phishing-URL
classification, with a citation. Not written here beyond the slot, per "do not
fabricate paper titles":

- **SVM**: `[CITATION NEEDED: SVM for phishing/malicious URL detection]`
- **Decision Tree**: `[CITATION NEEDED: decision-tree-based URL/phishing classifiers]`
- **Random Forest**: `[CITATION NEEDED: random forest for malicious URL detection]`
- **XGBoost**: `[CITATION NEEDED: gradient-boosted trees / XGBoost for phishing detection]`

### Item 3 — Features

Real feature list (73 features, `semd-ml/src/features/features.yaml`), grouped as
declared: URL-level (16), URL-level thresholds (5), domain-level (24 — the YAML's
own section-header comment says 22 and undercounts), path-level (11 — header says
10), query-level (13 — header says 10), pattern (3). **The YAML's own group-size
comments are stale** (16+5+22+10+10+3=66 vs. 73 actual `- name:` entries) — flag
this to the author as a documentation inconsistency in `semd-ml`, separate from the
thesis's own feature table.

**Extractability, verified by diff against `semd-ml/src/features/extractor.py`:**
all 73 YAML-declared features have a matching implementation
(`features["<name>"] = ...` assignment) in `extractor.py`. Confirmed no
WHOIS/DNS/network calls anywhere in the extraction path (`grep` for
`whois|dns|requests\.|socket\.|resolve|timeout` in `extractor.py` returns nothing) —
every feature is a pure string/regex/entropy computation over the URL text itself.
**Conclusion: none of the 73 features can fail to extract; all are used in both
train and test** (the same `FeatureExtractor.extract()` runs in both
`data/dataset_pipeline.py` and `ml/prediction_service.py`).

Full feature table (name | type | description | extractable | train | test) —
generate directly from `features.yaml` if a machine-readable table is needed; not
duplicated in full here since it's already correct at the source and would drift.

`class_feature_emphasis` in `features.yaml` names 2 "strong" benign features and 19
"strong" malicious features — these read as heuristic weights, not empirically
validated feature importances; if the thesis claims specific features are the most
predictive, that claim needs its own citation or an actual feature-importance run
(e.g. from the trained Random Forest/XGBoost models), not the YAML's hand-assigned
weights.

**Author must supply:** a citation per feature group (or per "critical"-priority
feature) framed around phishing/malicious-URL literature —
`[CITATION NEEDED: <feature category>]`.

### Item 5a — "if nullable, don't add a note"

Reviewed `docs/backend/database/table-dictionary.md`: it already expresses
nullability as a plain Yes/No column value, not as a written sentence in the
description column (no "(this field can be null)" style notes exist there today).
If the advisor's comment is about the **thesis's own** data-dictionary table (a
document outside this repo), the same rule — drop textual nullable notes, keep only
the Nullable column value — should be applied there directly; that document isn't
in this repo and wasn't found by grep, so it can't be edited from here.

## 6. Post-review fixes and open operational items

An independent review of the diff above (commit `7707eae`) found a Critical
authorization bypass, fixed in a follow-up commit (`f001b21`) on the same branch:
switching `/prediction/predict` to `user_id=None` for anonymous callers also
silently disabled the ownership check in `services/prediction_service.py` (the
leading `user_id and` made the whole guard short-circuit False whenever there was
no caller identity) — meaning an anonymous caller, or one with an expired token,
could use *any* `service_id`, including another user's private `ServiceConf` and
the third-party API credentials linked to it via `ThirdServiceConf.headers_json`.
Fixed by removing that leading conjunct so the ownership check applies to
anonymous callers exactly as it does to non-owning authenticated ones; covered by
a new test (`tests/unit/test_prediction_service_ownership.py`). Full suite is now
112 tests (86 original + 26 added across this fix and its own test coverage), all
passing.

A scoped re-review of that fix caught one more consequence of making the
ownership check correct: `control/prediction_control.py::_get_default_ml_service`
(used whenever a `/prediction/predict` request doesn't specify `service_id`)
picked the oldest active `ML_MODEL` row with no ownership filter at all. Once
the ownership check stopped silently skipping for anonymous callers, an
environment whose oldest `ML_MODEL` config happened to be MEMBER-owned would
have every anonymous (and every other non-owning) caller 403 on the default
path — silently defeating the entire point of this pass. Fixed in code rather
than left as an ops checklist item: the query now only ever selects a row that
`predict_with_service`'s ownership check would let *any* caller use — owner-less
(`user_id IS NULL`) or admin/super-admin-owned — via an `outerjoin` to `User`
filtered on role. Covered by
`tests/unit/test_prediction_control_default_service.py`. Full suite is now 115
tests, all passing.

Two items surfaced by the reviews still need action, listed here rather than
fixed silently:

**`semd-frontend`'s generated API client is stale beyond this pass's scope, and
regenerating it in full currently breaks the frontend build.** Attempting
`npm run generate:api` end-to-end (to drop the now-removed `gh_id`/`gg_re_token`
fields and the retired `github` enum value from the generated TypeScript client)
surfaced an unrelated, pre-existing backend bug: `PredictionDetailResponse` is
defined **twice** — `models/prediction/prediction_response.py` (generic,
`data: Any`-shaped) and `models/stats/prediction.py` (`data: list[PredictionDetailItem]`)
— and `routers/stat/prediction_stat_route.py` imports the generic one via
`models/__init__.py`'s re-export, not the properly-typed one. Orval faithfully
generates `data: unknown` for it, which breaks
`semd-frontend/src/services/scan.service.ts`'s `response.data.data.find(...)`
(fails `tsc --noEmit`). Since this is a real, unrelated backend contract bug —
not something to guess a fix for under this pass — the full client regeneration
was reverted rather than committed broken. **Confirmed harmless in the
meantime**: both this review and the prior one grepped `semd-frontend/src`
outside `generated/` for reads of `gh_id`/`gg_re_token`/the `github` enum value
and found none, so the stale generated types are a documentation/hygiene issue
only, not a runtime risk. Recommended order: fix the `PredictionDetailResponse`
naming collision first (decide which of the two class definitions the route
should actually use), then run a full `npm run generate:api` once, rather than
patching the generated file by hand.

**Companion commits, for completeness:** `semd-extension@bb32e6b` fixes a second,
separate client-side gate (`src/popup/index.tsx`) that also blocked the popup UI
entirely when no Access Code was configured — `9827da2` alone (removing the
`x-api-key` pre-flight block in `api.ts`) wasn't sufficient on its own to make the
extension actually usable without one. `semd-frontend@be986da` removes the
GitHub login button and its NextAuth provider wiring, since GitHub OAuth login no
longer exists on the backend (`libs/types/enums.py::OAuthProviderType`) as of
this pass — left broken otherwise (silent 422 on click).
