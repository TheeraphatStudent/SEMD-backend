# Feature: Browser Extension Access Codes

## Purpose (as implemented — not as originally envisioned)

`POST /setting/access-key/extension/token` (`routers/setting/access_key_route.py::create_extension_token`) generates a 6-character alphanumeric token, stores it on `User.ex_acc_token`/`ex_acc_token_exp`, and returns it once. That is the **entire implemented feature**. There is no separate router/service/control module for this domain — it lives inside the API Access Keys router because it shares that file, not because it's the same concept as an API key (the master prompt explicitly says to keep them separate unless the codebase says otherwise, and the codebase already keeps them structurally distinct: different storage column, different generation logic, different response shape).

## Finding: the feature is generation-only — no consumer exists anywhere

Grepped `ex_acc_token` across `semd-backend` (this repo), `semd-extension`, and `semd-frontend` (siblings at `/home/semd/Desktop/Project/SEMD/`). Zero hits outside this backend's generation code and the auto-generated `orval` TypeScript type in `semd-frontend/src/services/generated/models/userModel.ts` (which existed only because the leaked field was in the OpenAPI schema — see the secret-exposure fix below).

**There is no `/setting/access-key/extension/token/validate` (or any) exchange endpoint.** Nothing in this backend ever reads `User.ex_acc_token` back to authenticate or authorize a request — not `AuthGuard`, not any router. The browser extension does not call this endpoint. This means:

- The "Generate Access Code" half of Feature 4 exists; "Validate Access Code", "Exchange code for extension authorization", device/browser association, usage limits, and audit history (all listed in the master prompt's Feature 4 scope) **do not exist in any form**.
- I cannot safely design or implement the missing exchange/validation flow — the master prompt prohibits inventing requirements not found in the codebase or documentation, and there's no evidence anywhere (this repo, the extension repo, or the frontend repo) of what the intended exchange contract should look like (a JWT? a session cookie? treated as an API-key equivalent for extension-originated `/prediction/predict` calls?). **This is a "requirement cannot be determined from the codebase" stop condition** — flagged here rather than guessed at. Continuing to other domains since this doesn't block anything else; needs a product/spec decision before an exchange endpoint can be built.

## Fixed this pass (unambiguous, no product decision needed)

1. **Plaintext storage → hashed at rest.** `User.ex_acc_token` previously stored the raw generated token. Now stores `sha256(token)`, matching the `AccessKey` pattern from Domain 3. The client-visible response is unchanged (raw token still returned once, same 6-char format) — this only changes what lands in the database.
2. **Secret exposure via `UserModel` — the more severe finding, discovered while tracing this feature's data flow.** `models/user_model.py::UserModel` (the response schema for `GET /auth/me`, `PUT /auth/me`, `GET /auth/users`, `POST /auth/users`, `GET/PUT /auth/users/{id}`) included `password_hash`, `gg_acc_token`, `gg_re_token`, `gh_acc_token`, `gh_re_token`, `twofa_secret`, and `ex_acc_token` verbatim. This meant:
   - Every user could see their own live OAuth refresh tokens, TOTP secret, password hash, and extension token by calling `GET /auth/me`.
   - Every **ADMIN** could see every **other** user's same secrets via `GET /auth/users` / `GET /auth/users/{id}` — an admin-privilege-escalation-adjacent issue (an admin account compromise now also yields every user's OAuth refresh tokens and TOTP seeds, not just admin-scoped data).

   Fixed by removing those 7 fields from `UserModel` (verified via grep that no internal code reads secret fields off a `UserModel` instance — the ORM `User` object, not `UserModel`, is what internal auth logic actually uses; `UserModel.model_validate(orm_user)` exists purely for API serialization). Kept `gg_id`/`gh_id` (provider identifiers, not credentials — useful for a "connected accounts" UI) and `ex_acc_token_exp` (an expiry timestamp, not the secret itself).

Not fully "Domain 4 scope" by the master prompt's own feature boundary (the leak affects Auth/Users endpoints, not the extension-token endpoint itself) — fixed here because it was discovered while tracing `ex_acc_token`'s full lifecycle, and severity (live OAuth tokens + TOTP secrets exposed to every admin for every user) doesn't justify waiting for a later domain pass.

## OpenAPI contract impact — documented breaking change

`UserModel`'s schema lost 7 properties (`password_hash`, `gg_acc_token`, `gg_re_token`, `gh_acc_token`, `gh_re_token`, `twofa_secret`, `ex_acc_token`); 0 added. **Classification: Breaking, intentional, security-motivated.** Any client (web frontend, browser extension, external API consumer) that reads these fields from a user-profile response will now get `None`/missing instead of a value. Grepped `semd-frontend`/`semd-extension` source (excluding `node_modules` and generated code) for reads of these field names — none found beyond the auto-generated type definition itself, so no known active consumer breaks. Still recorded as breaking per the contract-diff rule ("do not accept accidental breaking changes" — this one is deliberate and documented, not accidental).

## Testing

- `tests/unit/test_user_model_no_secrets.py` — schema no longer declares the 7 secret fields; connected-account fields (`gg_id`, `gh_id`, `is_2fa_enabled`, `ex_acc_token_exp`) remain; `model_validate` still works against an ORM-shaped object.
- `tests/unit/test_access_key_error_handling.py::test_extension_token_stored_as_hash_not_plaintext` — DB-side value is `sha256(raw_token)`, not the raw token; response still returns the raw token once.

## Migration / rollback

`git checkout -- models/user_model.py routers/setting/access_key_route.py tests/unit/test_user_model_no_secrets.py tests/unit/test_access_key_error_handling.py`. No schema migration needed — `ex_acc_token` remains a `Text` column, now holding a hex digest instead of a raw string; no column type change. Existing users with a previously-generated plaintext token in that column will simply have an unusable-looking value until they regenerate (irrelevant in practice since nothing ever validated it anyway).

## Open item for product/spec owner

What should `POST /setting/access-key/extension/token` actually enable once generated? Needs an answer before Feature 4 can be called complete — right now it's a token that goes nowhere.
