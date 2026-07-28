# Session Handoff — SEMD Backend Audit/Refactor

For the next engineer or agent picking this up. Full detail lives in `SEMD_BACKEND_FINAL_HANDOFF.md` and the 38 docs under `docs/backend/`; this is the compact version.

## What happened

A 13-domain, security-focused audit-and-refactor of `semd-backend` (FastAPI malicious-URL-detection backend). Domain 1 (auth) was validated before this session's autonomous portion; Domains 2-13 (users/roles, API keys, extension codes, URL evaluation + SSRF, third-party services, reports, flags, dashboard/stats, ML registry, dataset/retraining, workers/Redis, audit logs, shared infra) were each run through the same loop: capture current behavior → fix typed-error handling and any authorization gap found → add characterization tests proving both success-path preservation and status-code correction → document. 86 unit tests exist, all passing. No schema migrations were performed. mypy (188 errors) and ruff (141 errors) baselines were measured, documented, and deliberately **not** cleared — they predate this engagement and clearing them would have meant an unscoped codebase-wide type migration, not a domain fix.

## The 3 most important things to know before touching this code

1. **Two auth-guard function identities must stay the same object.** `guard/auth_guard.py` assigns `AuthGuard.verify_bearer_token = staticmethod(_verify_bearer_token)` etc. deliberately — this is not stray code to "clean up." A prior bug had `Depends(get_current_user)` inside the class body resolve to a *different* object than `AuthGuard.get_current_user` accessed externally, silently breaking `app.dependency_overrides` in tests and any code relying on identity equality. If you refactor this file, re-verify with `AuthGuard.require_admin.__wrapped__ is _require_admin`-style identity checks, not just "the tests still pass" (the tests passed with the bug present too, until the identity check was added specifically to catch it).

2. **`routers/__init__.py`'s import order is load-bearing and ruff will silently break it.** `from .base_route import BaseRoute` must precede `from .auth import ...` because `routers/auth/auth_route.py` does `from routers import BaseRoute`, reaching into the partially-initialized package. Running `ruff check --fix` across this file alphabetizes imports and breaks it — caught once already via a 5-file `ImportError` cascade in the test suite. There's a `# noqa: I001` comment guarding it; don't remove it, and don't run blanket `ruff --fix` across the repo without checking this file's import order survives.

3. **The OpenAPI diff has a blind spot you must not repeat.** Path-set-only diffing (`set(before['paths']) - set(after['paths'])`) cannot see schema/response-body changes. It's how earlier per-domain checkpoints in this engagement under-reported the `UserModel` change as "additive only" when it's actually a breaking removal of 7 fields (`password_hash` and 6 other secret/token fields — Domain 3's fix for a real secret-exposure bug). The corrected structural diff is in `docs/backend/contracts/openapi.diff.md`. Separately: this codebase's routers mostly don't declare `responses={}`, so *no* diffing method — path-set or structural — will ever see runtime status-code changes (the 500→403 corrections, new 422 SSRF rejections, new 501 stubs). Those are only tracked in prose, per-domain, in `openapi.diff.md` §4. If you change a status code, update that section by hand; the tooling won't catch it for you.

## Where the highest-severity issues were (in case anyone asks "was this actually risky")

Ranked by what an attacker/bad actor could have done pre-fix:
1. **ML model registry (Domain 9)** — any authenticated MEMBER could point production prediction traffic at any model they registered. Now admin-gated. This is the single most severe finding of the whole engagement — it's the difference between "wrong stat on a dashboard" and "attacker controls what the malicious-URL detector actually says."
2. **SSRF (Domain 4)** — zero defense pre-fix; a submitted URL was fetched (third-party detector path) or used for prediction with no check against loopback/private/link-local/cloud-metadata targets, including via DNS rebinding (hostname resolves to a private IP at fetch time even if it looked public lexically). Fixed with lexical + live-DNS-resolution checks on every URL-accepting path.
3. **Report IDOR (Domain 2)** and **GLOBAL URL flags (Domain 7)** — any user could edit/delete any other user's report; any user could set a flag that changes results for every other user. Both now ownership/admin-checked.
4. **Secret exposure (Domain 3)** — `UserModel` was serializing `password_hash`, 4 OAuth tokens, and a 2FA secret directly into API responses (e.g. `GET /auth/users`). Removed from the model entirely.

Full findings table with fixed/open status for every one of these: `docs/backend/standards/SECURITY.md`.

## What's genuinely still broken or missing (don't assume these were fixed)

- `GET /report` / `GET /report/{id}` let any authenticated user view any other user's report — this is *unresolved*, not fixed. It's ambiguous whether it's an intentional shared-intel view or a bug; needs a product-owner call, documented but not decided.
- No audit logging exists anywhere — the `ActivityLog` table is defined in `database/models.py` and never written to. Verified by grep, not assumption.
- No dataset upload/validation/versioning exists; the admin-only retrain queue (`GET /queue/url`) and training-job submission (`POST /ml/training/submit`) are not connected — an admin has to manually bridge them today.
- Background-job payloads carry no schema version; failed job processing in `workers/prediction_worker.py` is silently dropped (no dead-letter queue). Both deliberately deferred — see `docs/backend/adr/0006-background-job-strategy.md` for why (mainly: fixing this from the `semd-backend` side alone risks breaking compatibility with `semd-ml`, a separate repo this session couldn't verify against).
- `services/url_report_service.py::update_report` does two non-atomic sequential commits — a real but low-observed-impact inconsistency window. See `docs/backend/adr/0003-database-transaction-strategy.md` for why it wasn't folded into the Domain 2 fix that touched the same file.

## Validation status — read literally, not optimistically

- **Tests: 86/86 passing.** `uv run python -m unittest discover -s tests/unit -p "test_*.py"` (this repo uses `unittest`, not pytest — no pytest config exists).
- **Typecheck: 188 mypy errors.** Pre-existing baseline, unchanged by this engagement. Dominant cause: legacy `Column(...)`-style SQLAlchemy models typed as `Column[T]` where code expects `T` — a systemic pattern, not scattered typos. Fixing it means migrating to `Mapped[]`/`mapped_column()`, out of scope here.
- **Lint: 141 ruff errors.** Same status. 128 are auto-fixable but blind `--fix` is unsafe (see point 2 above) — review file-by-file if you tackle this.
- **No live integration testing.** No Postgres/Redis/`semd-ml` instance was available in this environment. Everything validated here is unit-level or in-process (`TestClient`). Don't treat this handoff as claiming end-to-end verification against real infrastructure — it explicitly isn't.

## If you're picking up the next piece of work

Recommended order, from `SEMD_BACKEND_FINAL_HANDOFF.md` §16: (1) get a product-owner decision on report visibility, (2) build real audit logging, (3) adopt Alembic before the next schema change, (4) coordinate with `semd-ml` on payload versioning, (5) a dedicated transaction-boundary pass with forced-failure tests, (6) `Mapped[]` migration to shrink the mypy baseline, (7) close the dataset/retrain-queue gap. None of these were started — they're prioritized findings, not partial implementations.

## Mobile

Explicitly out of scope per this engagement's instructions — discontinued, not implemented/restored/tested/documented. Shared endpoints with mobile history were left in place; nothing mobile-specific exists in the current codebase to accidentally revive.

## Key file map for orientation

- `docs/backend/SEMD_BACKEND_FINAL_HANDOFF.md` — full 17-section handoff (this file's parent doc).
- `docs/backend/features/*/README.md` — one per domain, each with before/after, tests, embedded Mermaid diagrams where relevant.
- `docs/backend/standards/SECURITY.md` — the cross-domain findings table; start here if triaging "what's actually still risky."
- `docs/backend/standards/TESTING.md` — full 19-file/86-test inventory and explicit coverage gaps.
- `docs/backend/contracts/openapi.before.json` / `openapi.after.json` / `openapi.diff.md` — contract diff, corrected for the schema blind spot described above.
- `docs/backend/adr/` — 5 ADRs recording deliberate non-fixes with reasoning (read before "fixing" any of them without checking whether it was already considered and deferred for a specific reason).
