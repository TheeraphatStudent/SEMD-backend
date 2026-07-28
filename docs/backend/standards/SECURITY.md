# Security Standard

Consolidates every security finding surfaced across Phase 1 (audit) and Phase 4 (Domains 1-13). Findings are grouped **fixed** vs. **open** — this is the authoritative list for a security sign-off, not any single domain checkpoint.

## Fixed this engagement, by severity

| Severity | Finding | Domain | Fix |
|---|---|---|---|
| Critical | Any MEMBER could register/promote/activate an ML model with attacker-controlled artifact URIs, redirecting all production prediction traffic | 10 | `AuthGuard.require_admin` on all 7 mutating `/ml/models*` endpoints |
| Critical | Any MEMBER could create a `GLOBAL`-access-level URL flag, affecting every user's prediction annotation; only the creator (never an admin) could remove one | 8 | Admin-required for GLOBAL flag create/edit; admin-or-owner for delete |
| High | `UserModel` (backing `/auth/me`, `/auth/users*`) returned `password_hash`, live Google/GitHub OAuth refresh tokens, TOTP secret, and the extension token in cleartext to the profile owner and to any admin viewing any other user | 4 | 7 fields removed from the response schema |
| High | Broken object-level authorization: any MEMBER could edit or silently change the review status of any other user's URL report | 2 | Ownership + admin-only status-change check |
| High | 15/22 auth endpoints silently converted typed `401`/`403`/`404` business errors into generic `500`s (missing `except HTTPException: raise` guard before a catch-all) — systemic pattern, found again in report/access-key/flag routers | 1-8 | Redundant router-level `try/except` removed; global handler + typed `AppError`s propagate correctly |
| High | Global exception handler leaked raw `str(exception)` (SQL text, internal paths, connection strings) to clients on unexpected errors | 1 (foundation) | `core/error_handlers.py` logs server-side, returns a generic message |
| High | `third_service_executor.py` leaked vendor response bodies and connection-error text (potentially including vendor secrets) to any MEMBER via `/prediction/predict`, not just the admin who owns the third-party integration | 6 | Generic `ExternalServiceError`/`ServiceUnavailableError` to caller, real detail logged server-side |
| Medium | TOTP secrets stored in plaintext at rest | 1 (audited, not fixed — see Open below) | — |
| Medium | Extension access token stored in plaintext (unlike properly-hashed API keys) | 4 | `sha256` hash at rest, matching `AccessKey` pattern |
| Medium | `GET /queue/url` exposed other users' username/user_id/profile image tied to specific URLs they predicted, to any MEMBER | 11 | Gated to admin |
| Medium | No SSRF/scheme/private-IP/DNS-rebinding validation on user-submitted URLs before forwarding to the ML queue or third-party detectors — two independent entry points, both unprotected | 5 | `core/security.py::reject_unsafe_urls` wired into both `PredictionControl` and `MLPredictionService` |
| Low | `DELETE /setting/third-service/{id}` crashed with a 500 on every call (`BaseResponseModel(status="success", ...)` against an `int`-typed field) | 6 | `status=200` |
| Low | Stray `print(e)` debug statement in production error path | 6 | Replaced with `logger.warning` |
| Info | 32 Dashboard/Stat endpoints + `GET /ml/service` were unauthenticated `pass` stubs, unconditionally crashing on every call | 9, 10 | Authenticated, honest `501` |

## Open, documented, not fixed — with reasoning

| Finding | Why not fixed here |
|---|---|
| TOTP secrets stored in plaintext at rest (`User.twofa_secret`) | Needs an encryption-at-rest design decision (app-level envelope encryption vs. DB-level column encryption, key management) — a genuine architecture choice, not a mechanical fix |
| OAuth `state` parameter generated but not verified on callback (CSRF gap in the OAuth login flow) | Needs a server-side state store (Redis, short TTL) design — same category, not mechanical |
| No rate limiting anywhere in the API (login, TOTP verification, refresh-token exchange, prediction, all of it) | No rate-limiting infrastructure exists at all; introducing one (library choice, storage backend, per-endpoint limits) is a cross-cutting infrastructure decision, not a per-domain fix |
| File/CSV upload validation for `/prediction/predict`'s `text_file`/`csv_file` (size limits, content-type checks) | Flagged in Phase 1, not re-verified or fixed in Phase 4 — no domain in the 13-domain sweep owned this specific endpoint's upload path in depth |
| `third_service_executor.py`'s response-size guard is post-fetch, not a true streaming cap (a server that lies about `Content-Length` and never sends one isn't protected against memory exhaustion) | Documented limitation from Domain 5; a true fix needs a `client.stream()` rewrite of that call, deferred as lower-priority since `base_url` there is admin-configured, not attacker-controlled |
| No audit-log coverage for 10 of 11 required event categories (role changes, API-key lifecycle, model activation, flag changes, etc.) | Domain 13 finding — needs a new table + shared helper + wiring into ~15-20 call sites; scoped as a recommendation, not built, to avoid a half-covered implementation |
| Dead code: unused `PyJWT` dependency alongside actually-used `python-jose`; unused `jwt_secret`/`jwt_algorithm` settings fields | Housekeeping, not a vulnerability — noted, not removed (low value, no urgency) |
| `database/models.py` FK cascade behavior for `url_reported.user_id` (`ON DELETE SET NULL` combined with `NOT NULL` in the same column — contradictory, would fail at delete time) | Pre-existing DDL bug found while adding `ForeignKey()` declarations in Phase 3; matched as-is to reflect current DB behavior rather than silently "fixed" without confirming which side (nullable vs. cascade rule) is actually wanted |

## SSRF posture (Domain 5, full detail in that domain's doc)

This backend never fetches URL content itself — both prediction entry points forward the URL string to `semd-ml` (via Redis) or to an admin-configured third-party detector. The validator (`core/security.py`) covers: scheme allow-list, embedded-credential rejection, literal private/loopback/link-local/CGNAT/metadata-IP rejection, numeric-encoded-host rejection, and DNS resolution with resolved-IP checking (closing the rebinding gap). It does **not** and cannot cover active-fetch concerns (redirect chains, response size during a fetch, fetch timeouts) for the *submitted* URL, because this backend doesn't fetch it — those concerns belong to `semd-ml` (out of this repo) and were applied instead to `third_service_executor.py`, the one real outbound-fetch path that does exist here.

## Auth/crypto posture confirmed correct (not re-litigated per domain)

Bcrypt password hashing, generic invalid-credential messages (no username enumeration), refresh tokens hashed at rest (`sha256`), API keys hashed at rest (`sha256`, shown once), object-level ownership checks correct in the Access Keys and Third-Party Services domains (unlike Reports/Flags, which had real bugs — see above).
