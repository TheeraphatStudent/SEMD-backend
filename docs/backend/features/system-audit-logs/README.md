# Feature: System and Audit Logs (Domain 13)

No code changes in this domain — findings only, per the same reasoning as Domains 9 and 11: building a real audit-logging system now, this late in a 13-domain pass, risks a half-covered implementation that looks more complete than it is. Documented precisely instead.

## Application logs — done (Phase 3, not this domain)

Structured JSON logging (`core/logging.py`) with request-ID correlation (`core/middleware.py::RequestContextMiddleware`) was built in Phase 3 and is wired into every request via `application.py`. This satisfies the master prompt's "application logs" half of Domain 13 (runtime diagnostics, exceptions, performance, dependency failures) — already covered, not re-verified line-by-line here since Phase 3's checkpoint already validated it (see `tests/unit/test_core_error_handlers.py`, which asserts the unhandled-exception path logs server-side).

## Audit logs — the actual gap in this domain

Two tables exist that could serve an audit purpose:

- **`ActivityLog`** (`database/models.py:185-199`): `user_id`, `method`, `endpoint`, `request_id` (unique), `client_ip`, `client_agent`, `response`, timestamps. **Confirmed via repo-wide grep: this table is never written to anywhere in the codebase.** The SQLAlchemy model and its Pydantic counterpart (`models/activity_log_model.py`) exist, but no `ActivityLog(...)` is ever constructed or `db.add()`'d. It's schema-only, unused since whenever it was added.
- **`UsageLog`** (`service_id`, `access_key_id`, `prediction_id`, `type`): actually populated, via `services/usage_log_service.py`, called from `control/prediction_control.py` on every prediction. But its scope is narrow — API/prediction usage counting, not a general audit trail (no actor-vs-target distinction, no before/after state, no admin actions).
- **`url_reported`**: the one genuine domain-specific audit trail that exists and works — every `url_report` status/field change is logged via `UrlReportService._log_action` (action, old_status, new_status, remark, actor `user_id`, timestamp). This is the pattern the rest of the system should follow, not a special case to leave alone.

### What the master prompt's required audit-event list actually has coverage for, confirmed by grep

| Required audit event | Coverage |
|---|---|
| Authentication events (login, logout, token refresh/revoke) | **None** |
| Role changes | **None** — `AuthService.admin_update_user` changes `target_user.role` with zero logging (grepped `control/`, `services/auth_service.py` for `logger.`/audit calls around role changes: zero hits) |
| Account changes (create/update/delete/suspend) | **None** |
| API-key creation and revocation | **None** — `services/access_key_service.py` has no logging around key lifecycle events |
| Access Code (extension token) creation and revocation | **None** |
| URL-report decisions | **Covered** — `url_reported` table, `_log_action` |
| Flag changes (Domain 8) | **None** — the GLOBAL-flag permission fix in this pass added authorization, not audit logging; creating/editing/deleting a `url_flag` is silent |
| Detection-service changes (Domain 6) | **None** |
| Model activation (Domain 10) | **None** — `promote_to_production`/`activate_model`/`deactivate_model`, now admin-gated, still have zero audit trail of *which* admin activated *which* model *when* |
| Dataset changes | N/A — no dataset management exists (Domain 11 finding) |
| Training actions (Domain 10/12) | **None** — `MLTrainingRouter`'s newly-wired, admin-gated endpoints don't log who submitted a training job |

**Net: 1 of 11 required audit-event categories has real coverage.** This is a genuine, sizable gap — not a bug in any single domain, but a missing cross-cutting capability that should have been built once in Phase 3 (foundation) and wired into each domain's mutation call sites as they were touched, the same way `core/exceptions.py`/`core/security.py` were.

## Recommendation for closing this gap (not built here)

1. Add a real audit table matching the master prompt's fields (`actor_user_id`, `action`, `resource_type`, `resource_id`, `previous_state` JSON, `new_state` JSON, `request_id`, `source_ip`, `created_at`) — either repurpose `ActivityLog` (would need a migration: it's missing `action`/`resource_type`/`resource_id`/before-after-state columns entirely, so "repurpose" really means "redesign") or add a new `audit_log` table. Given `ActivityLog` is unused and schema-mismatched to the actual need, a fresh table is likely cleaner than retrofitting it.
2. Add a small `core/audit.py` helper (`log_audit_event(db, actor, action, resource_type, resource_id, previous_state=None, new_state=None)`) that reads `request.state.request_id` (already available from `core/middleware.py`) — mirroring how `core/security.py`/`core/exceptions.py` were added as shared Phase-3 infrastructure.
3. Wire it into each of the ~15-20 mutation call sites identified in the table above, prioritizing the highest-severity ones first: model activation (Domain 10, the audit's single highest-severity finding), role changes, API-key/access-code lifecycle.
4. This is foundation-shaped work (belongs conceptually in Phase 3) being surfaced at the end of Phase 4 because that's when its absence became fully visible across every domain — not a criticism of the phase ordering, just where the evidence accumulated.

## Testing / migration / rollback

No code changed in this domain — nothing to test or roll back.
