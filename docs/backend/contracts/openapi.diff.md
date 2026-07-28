# OpenAPI Diff: before → after

Source: `docs/backend/contracts/openapi.before.json` (captured Phase 1, pre-refactor) vs. `docs/backend/contracts/openapi.after.json` (captured post-Domain-13, via `make openapi` against the final `main.py`).

This is a **structural** diff (paths, `components.schemas` property sets, per-path declared response status codes) — not the path-set-only comparison used in earlier per-domain checkpoints. That earlier method could not see schema or response-body changes; this one does, and it changes the classification of at least one item below (`UserModel`) from what individual checkpoints implied.

## 1. Path changes

**Added (5):**

| Path | Method(s) | Domain | Classification |
|---|---|---|---|
| `/health/live` | GET | Phase 3 infra | Additive |
| `/health/ready` | GET | Phase 3 infra | Additive |
| `/ml/training/submit` | POST | 10 | Additive — router existed in code but was never registered/reachable before this refactor. Not a new capability being exposed for the first time in terms of code that existed; new in terms of what's *reachable*. |
| `/ml/training/result` | POST | 10 | Additive (same reasoning) |
| `/ml/training/retrain` | POST | 10 | Additive (same reasoning) |

**Removed:** none.

## 2. Schema changes

**Added schemas (3):** `JobResultRequest`, `TrainingJobRequest`, `TrainingJobResponse` — all backing the newly-registered `/ml/training/*` routes. Additive.

**Changed schemas (2):**

### `MLPredictResponse` — Additive
Added fields: `feature_schema_version`, `is_malicious`, `model_alias`, `model_version`, `prediction_time_ms`. No fields removed. Backward-compatible for existing consumers that don't read these fields.

### `UserModel` — **Breaking**
Removed fields: `password_hash`, `gg_acc_token`, `gg_re_token`, `gh_acc_token`, `gh_re_token`, `twofa_secret`, `ex_acc_token`. No fields added.

This is an unambiguous breaking response-schema change, fixed in Domain 4 (`docs/backend/features/extension-access-codes/README.md`) after discovering the model was serializing password hashes, OAuth tokens, and 2FA secrets directly into API responses everywhere `UserModel` was returned (e.g. `GET /auth/users`, `GET /auth/me`). **Earlier per-domain checkpoints, which used a path-set-only diff, reported the overall OpenAPI change as "additive only" — that was incomplete.** Path-set diffing cannot see schema property changes; this document is the first point in the engagement where a structural diff was run, and it corrects that gap. Any client currently reading these 7 fields off a user object will break. This is intentional and documented as a required security fix, not an oversight.

## 3. Declared response status codes per path/method

Zero changes. Every path/method common to both snapshots declares the identical set of status codes in `responses={}` before and after.

This is expected, not a sign that nothing changed at the response-code level — see §4.

## 4. Behavioral contract changes NOT visible in the OpenAPI schema

The schema diff above is necessarily incomplete for this codebase: **routers in this project generally don't declare a `responses={}` dict**, so the actual set of status codes an endpoint can return was never part of the generated OpenAPI document, before or after. FastAPI/OpenAPI only documents what's explicitly declared; it does not introspect handler bodies for `raise` statements. The refactor changed a substantial number of *runtime* status codes without touching any schema. These are enumerated per-domain in each `docs/backend/features/*/README.md`; consolidated here:

**Corrections to a previously-broken contract (bug fixes — the documented behavior was already "should be a typed error," the runtime just didn't do it):**
- Numerous `except Exception: raise HTTPException(500, str(e))` sites converted to typed `AppError` subclasses, so already-typed errors (`HTTPException`, validation failures, not-found, conflict) stop being swallowed and re-emitted as 500. Full inventory: `docs/backend/standards/SECURITY.md` and each domain's checkpoint.
- `DELETE /setting/third-service/{id}` — was an unconditional 500 (invalid `BaseResponseModel(status="success", ...)` construction, `status` is typed `int`) on every call; now returns 200. Domain 6.

**New rejections — intentional, documented breaking changes to what was previously silently accepted:**
- `POST /prediction/predict`, `POST /ml/predict`, `POST /ml/predict/batch` — now return `422` (`code: UNSAFE_URL`) for loopback/private/link-local/metadata-endpoint/localhost-alias/encoded-IP hosts and hostnames that resolve to any of those via live DNS lookup. Previously forwarded silently. Domain 5, `docs/backend/features/url-evaluation/README.md`.
- `POST /setting/url-flag`, `PUT /setting/url-flag/{id}` with `access_level: GLOBAL` — now require admin (`403` for non-admin), previously any authenticated MEMBER could set a flag affecting every user. Domain 8.
- `POST/PUT/PATCH/DELETE /ml/models*` — now require admin (`403` for non-admin MEMBER), previously any authenticated user could redirect production prediction traffic. Domain 10.
- `GET /queue/url` — now requires admin, previously any authenticated user could see other users' prediction activity. Domain 11.
- All 24 dashboard/statistics endpoints — now return `501 NOT_IMPLEMENTED` with an explicit message instead of whatever placeholder/broken behavior existed before (several returned fabricated zero-value stats). Domain 9.

**Classification:** the "new rejections" group is intentional, security-motivated, and breaking for any client currently depending on the old (insecure) behavior — this is a deliberate contract change, not an accident. The "corrections" group restores the contract to what was already documented/intended (a 4xx for a 4xx-shaped failure) rather than changing intended behavior. Neither group is visible in §1-3 above; both are real client-visible differences and are the primary reason this document cannot be read as "5 additive paths, 2 schema changes, done."

## 5. Summary table

| Change type | Visible in schema diff? | Count | Breaking? |
|---|---|---|---|
| New paths | Yes | 5 | No |
| New schemas | Yes | 3 | No |
| `MLPredictResponse` fields added | Yes | 5 fields | No |
| `UserModel` fields removed | Yes | 7 fields | **Yes** |
| Declared response codes changed | Yes (none found) | 0 | — |
| Runtime status-code corrections (500→correct code) | **No** | ~13+ sites across domains 2,3,6,8 | No (restores documented contract) |
| Runtime new rejections (403/422/501) | **No** | 6 endpoint groups, dozens of routes | **Yes**, by design |
