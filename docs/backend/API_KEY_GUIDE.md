# API Access Key Guide

## Creating and using a key

`POST /setting/access-key` (self-service, authenticated) or `POST /setting/access-key/admin` (admin, creates a key for another user with a usage limit). The response includes the raw key **exactly once** — it is never retrievable again; only its hash is stored. Losing it means resetting (`POST /setting/access-key/{key_id}/reset`), which invalidates the old key and issues a new one.

## Usage limits and tracking

`usage_limit` on the key row; actual usage tracked via the `usage_log` table (populated on every prediction that used the key, via `services/usage_log_service.py`). Query your own usage: `GET /setting/access-key/{key_id}/usage`, `/usage/monthly`, `/usage/yearly`. Object-level authorization here is correct and confirmed — you can only see usage for a key you own (`control/access_key_control.py` checks `key.user_id != user.user_id → 403` before returning anything), unless you're an admin using the `/admin/{key_id}/usage*` variants.

## Admin management

`GET /setting/access-key/admin` (list all), `PUT /setting/access-key/admin/{key_id}` (activate/deactivate, change limit), `DELETE /setting/access-key/admin/{key_id}`.

## What this is NOT

This is a **different mechanism from the browser-extension access token** (`POST /setting/access-key/extension/token`) — different storage column, different generation logic, no shared code path. Don't conflate the two when integrating. See `docs/backend/features/extension-access-codes/README.md` for the extension token's (currently incomplete) story.

## Security notes

Hash-at-rest confirmed correct (`sha256`, matches the mandate's "never store plaintext" requirement) — this domain was the reference pattern the extension-token fix (Domain 4) was brought in line with. No rate limiting on key creation or usage-query endpoints.
