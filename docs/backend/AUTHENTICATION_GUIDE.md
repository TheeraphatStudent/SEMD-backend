# Authentication Guide

## Flows available

- **Register + login**: `POST /auth/register`, `POST /auth/login` (returns a token pair, or a pre-auth token if 2FA is enabled on the account).
- **2FA**: `POST /auth/2fa/setup` (authenticated — generates a TOTP secret + QR URI), `POST /auth/2fa/enable` (verifies a code to turn it on), `POST /auth/login/2fa` (completes login after a pre-auth challenge).
- **OAuth**: Google and GitHub, both an authorization-code flow (`POST /auth/oauth/authorize` → redirect → `GET /auth/callback/{provider}`) and a device-code flow (`POST /auth/oauth/device` → `POST /auth/oauth/device/poll`) for GitHub.
- **Token refresh**: `POST /auth/refresh` (exchanges a refresh token for a new pair). **Rotation-on-use and replay-prevention were not independently re-verified in Phase 4** — flagged in Phase 1 as needing confirmation, not re-checked in this pass.
- **Logout**: `POST /auth/logout` (revokes the refresh token).
- **Profile**: `GET`/`PUT /auth/me`.

## What's cryptographically solid, confirmed

- Passwords: bcrypt (`passlib`).
- Login failures: generic message, no username enumeration.
- Refresh tokens: JWT with a `jti`, persisted as `sha256(token)` — not plaintext.
- API access keys: `sha256` hash at rest, raw key shown once.

## What's NOT solid, confirmed and unfixed (see `standards/SECURITY.md` for the full list)

- **TOTP secrets are stored in plaintext** (`User.twofa_secret`). If this matters for your deployment's threat model, don't rely on 2FA as a strong control until this is addressed — a DB read reveals every account's live TOTP seed.
- **OAuth `state` is generated but not verified on callback** — the CSRF protection the `state` parameter is supposed to provide isn't actually enforced end-to-end. Confirmed by tracing both `services/oauth_service.py` (only ever sends `state` outbound) and `control/auth_control.py::handle_oauth_callback` (accepts it with no stored-state comparison).
- **No rate limiting** on login, 2FA verification, or refresh-token exchange.

## Response-shape note (fixed in this refactor)

`GET /auth/me`, `GET /auth/users`, `GET /auth/users/{id}` previously returned `password_hash`, live OAuth refresh tokens, the TOTP secret, and the extension token in the response body — fixed (see `docs/backend/features/extension-access-codes/README.md`, the domain where this was found). If you're an existing client that read any of those fields, you'll need to stop — they're gone from the schema now, deliberately.

## Status-code note (fixed in this refactor)

Auth endpoints previously returned `500` for what should have been `401`/`400`/`403` (a systemic router bug — see `standards/ERROR_HANDLING.md`). If your client special-cased `500` responses from auth endpoints, that behavior is now dead code; you'll get the correct status the OpenAPI schema always documented.
