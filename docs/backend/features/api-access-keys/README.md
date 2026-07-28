# Feature: API Access Keys

## Purpose

Long-lived API keys for external/programmatic consumers, distinct from JWT session tokens and from the browser-extension access token (Domain 4). Endpoints: `routers/setting/access_key_route.py` (prefix `/setting/access-key`) → `control/access_key_control.py` → `services/access_key_service.py` → `database/models.py::AccessKey`.

## Already correct (verified, not changed)

- **Storage**: `secrets.token_urlsafe(32)` generated, only `sha256(raw_key)` persisted (`services/access_key_service.py`), raw key returned once at creation/reset. Matches the mandate's "store only a secure hash" / "display key once" requirements.
- **Object-level authorization**: `get_key_usage_monthly`/`yearly`/`all_time` already correctly check `key.user_id != user.user_id → 403` before this pass (`control/access_key_control.py:55,68,81`) — unlike `url_report`, this domain had the ownership check right from the start.

## Error-handling sweep

13 of 14 router methods used the pure-passthrough `except Exception → HTTPException(500, str(e))` pattern (11 already had the `except HTTPException: raise` guard, so only `get_my_keys` had a live mangling gap — and nothing in its call chain raises `HTTPException` today, so no regression case existed to characterize, only a future-proofing fix). All 13 stripped.

**One site kept its try/except intentionally**: `create_extension_token` does `db.commit()` directly in the router (the only method in this file that doesn't delegate persistence to a service) and had `db.rollback()` in its except block. Per the "preserve meaningful cleanup" rule, the rollback stays; only the `str(e)` leak is fixed (`except Exception: db.rollback(); raise`, letting the global handler format and log it).

## Client-visible changes

None to successful responses. No status-code corrections found in this domain (unlike auth/reports) because the guard pattern was already mostly correct here — this domain is evidence the bug wasn't universal, just common.

## Testing

`tests/unit/test_access_key_error_handling.py`: ownership-check 403 still passes through correctly post-sweep, admin-gate 403 for non-admin, and the extension-token rollback fires with no leak on a simulated commit failure.

## Deferred to Domain 4

`create_extension_token`'s own logic (plaintext `ex_acc_token` storage, 6-char/~35.7-bit token, no rate limiting on this endpoint) is a Phase-1-flagged finding but is Domain 4's (Browser Extension Access Codes) scope, not touched here beyond the error-handling fix.

## Migration / rollback

`git checkout -- routers/setting/access_key_route.py tests/unit/test_access_key_error_handling.py`. No DB/service-layer changes.
