# Transaction Boundaries

## Session lifecycle

`guard/auth_guard.py::get_db()` (sync) / `get_async_db()` (async) — both are FastAPI generator dependencies: create a session, `yield` it, `close()` in a `finally` block. `Session.close()`/`AsyncSession.close()` internally rolls back any uncommitted transaction, so a request that raises an exception without explicitly committing leaves no partial writes — confirmed this is what makes it safe that most exception paths in this codebase don't call `db.rollback()` explicitly (see the one exception, `create_extension_token`, discussed below).

## Where commits actually happen: the service layer, not application-level

Every domain audited in this refactor calls `db.commit()` directly inside `services/*_service.py` methods (`url_report_service.py`, `url_flag_service.py`, `auth_service.py`, `access_key_service.py`, etc.) — **not** centralized at a control/application-service transaction boundary the way `SEMD_BACKEND_TARGET_ARCHITECTURE.md`'s target layer responsibilities describe ("Application services should control business transaction boundaries... do not commit independently inside every repository method"). This is the actual, current pattern across the whole codebase, not something any single domain's fix changed — flagged here as the honest baseline, not silently declared "target-compliant."

**Practical consequence**: a `control/*_control.py` method that calls two service methods in sequence gets two separate commits, not one atomic transaction. Example: `UrlReportControl.update_report` → `UrlReportService.update_report` does the report update commit **and** the `_log_action` audit-row commit as two separate `db.commit()` calls inside the same service method (not even two different service calls — literally sequential commits within one method). If the second commit failed after the first succeeded, the report would show as updated with no matching audit-history row — an inconsistency window that exists today, not introduced by this refactor's changes (the pattern predates every domain fix made here).

## Rollback usage

Explicit `db.rollback()` calls are rare in this codebase. Found and preserved (not stripped) during the error-handling sweep: `routers/setting/access_key_route.py::create_extension_token`, the one router method that commits directly (mutating `current_user` in-place) rather than delegating to a service — its `except Exception: db.rollback(); raise` was kept specifically because it's meaningful cleanup, unlike the ~55 other router-level `except Exception` blocks removed across Domains 1-11, which were pure pass-through with no cleanup logic (verified per-site, not assumed).

## Async vs. sync sessions

Both exist side-by-side: `get_db()`/`Session` (sync, SQLAlchemy ORM `Query` API) used by most domains (auth, access keys, reports, flags, third-party services); `get_async_db()`/`AsyncSession` (async, `select()`/`await db.execute()`) used by prediction, ML model registry, and third-party service execution — wherever the call chain needs to `await` something else (an outbound HTTP call, a Redis poll) in the same request. No domain mixes both within one request in the code reviewed.

## Recommendation, not applied

Moving commit control to the control layer (one commit per use-case, not per service-method) would close the report/audit-row inconsistency window above and match the target architecture's stated intent. This touches transaction structure in every service file across every domain — a cross-cutting refactor bigger than any single domain's charter in this pass, and higher-risk to do quickly than the current inconsistency's actual observed impact (no data-corruption incident evidence exists; this is a theoretical window, not a reported bug). Recommended as a dedicated follow-up with its own testing pass (specifically: forced-failure tests injecting a commit failure between the two calls, to prove the fix actually closes the window), not bundled into this refactor.
