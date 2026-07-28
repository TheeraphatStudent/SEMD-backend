# Admin API Guide

Consolidated list of every admin-gated endpoint, why it's gated, and when that gate was added (several were added during this refactor — previously these were reachable by any authenticated MEMBER).

## Permission model

Two roles above `MEMBER`: `ADMIN`, `SUPER_ADMIN` (`libs/types/enums.py::RoleType`; a fourth value, `GUEST`, is defined but never used anywhere — dead enum value, not a real tier). `AuthGuard.require_admin` (added Domain 10) is the shared dependency for `role in (ADMIN, SUPER_ADMIN)`; three older per-router hand-rolled equivalents still exist and haven't been migrated to it (`routers/auth/user_route.py`, `routers/setting/system_config_route.py`, `routers/setting/access_key_route.py` each have their own `_check_admin*` method — functionally identical, just not consolidated).

`SUPER_ADMIN`-only (stricter than plain admin) for a handful of operations: creating another `ADMIN` user, changing a user's `role` field, editing/deleting a `SUPER_ADMIN` account, resetting a `SUPER_ADMIN`'s password.

## Admin-only endpoints, by domain

| Endpoint(s) | Domain | Since |
|---|---|---|
| `GET/POST /auth/users`, `GET/PUT/DELETE /auth/users/{id}`, `POST /auth/users/{id}/reset-password` | Users | Pre-existing |
| `POST /auth/create` (create ADMIN) | Users | Pre-existing, SUPER_ADMIN only |
| `GET/POST/PUT/DELETE /setting/access-key/admin*` | Access Keys | Pre-existing |
| `GET/PUT /setting/system-config` (write) | System Config | Pre-existing |
| `POST/PUT /setting/url-flag` **with `access_level: GLOBAL`** | URL Flags | **Added Domain 8** — previously any MEMBER could set this |
| `POST /ml/models`, `PUT /ml/models/{id}`, `PATCH /ml/models/{id}/stage`, `POST /ml/models/{id}/promote`\|`/activate`\|`/deactivate`, `DELETE /ml/models/{id}` | ML Model Registry | **Added Domain 10** — previously any MEMBER could redirect production prediction traffic |
| `POST /ml/training/submit`\|`/result`\|`/retrain` | ML Training | **Added Domain 10** — router was previously completely unregistered; wired up admin-gated from the start |
| `GET /queue/url` | Retrain Queue | **Added Domain 11** — previously any MEMBER could see other users' prediction activity |

## Not admin-gated, and confirmed correct to leave that way

Read-only ML endpoints (`list_models`, `get_model`, `get_production_model`) and prediction endpoints (`predict_url`, `predict_batch`) — viewing model metadata or requesting a prediction isn't the privileged operation; changing what model serves predictions is.

## Not admin-gated, flagged as unresolved (not this refactor's call to make)

`GET /report`, `GET /report/{id}` — any authenticated user can currently list/view any other user's report. Plausibly intentional (a shared threat-intel view) or a bug — genuinely ambiguous from the code, documented in `docs/backend/features/users-roles-permissions/README.md`, not decided.
