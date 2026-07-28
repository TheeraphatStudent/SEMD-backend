# SEMD Backend — API Overview

Entry point for API consumers (web frontend, browser extension, external API consumers). For implementation-level detail, see the per-domain docs in `docs/backend/features/`; for conventions, see `docs/backend/standards/API_CONVENTIONS.md`.

## Base URL and docs

Root path `/api` (reverse-proxy/deployment level). Interactive docs at `/docs`, OpenAPI schema at `/openapi.json`. `openapi.yaml` at the repo root is generated output (`make openapi`) — not hand-edited, not necessarily current between runs.

## Domains and their routers

| Domain | Prefix | Guide |
|---|---|---|
| Authentication | `/auth` | `AUTHENTICATION_GUIDE.md` |
| Users, roles, admin | `/auth/users` | `ADMIN_API_GUIDE.md` |
| API access keys | `/setting/access-key` | `API_KEY_GUIDE.md` |
| Browser extension token | `/setting/access-key/extension/token` | `docs/backend/features/extension-access-codes/README.md` — **generation-only, no consumer exists yet, see that doc** |
| URL evaluation | `/prediction`, `/ml/predict*` | `URL_EVALUATION_GUIDE.md` |
| Third-party detection config | `/setting/third-service`, `/setting/service` | `docs/backend/features/third-party-detection-services/README.md` |
| URL reports | `/report` | `docs/backend/features/url-reports/README.md` |
| URL flags / whitelist | `/setting/url-flag` | `docs/backend/features/url-flags-whitelist/README.md` |
| Dashboard / stats | `/dashboard`, `/stat/*` | **Not implemented** — see below |
| ML model registry / training | `/ml/models*`, `/ml/training/*` | `ML_OPERATIONS_GUIDE.md` |
| Retrain queue | `/queue/url` | `docs/backend/features/dataset-retraining/README.md` — admin-only |
| Health | `/health`, `/health/live`, `/health/ready` | — |

## Dashboard/Stat endpoints — honest status

All 32 `/dashboard/*` and `/stat/*` endpoints are registered, authenticated, and return `501 Not Implemented` — they are not stubs pretending to work; every call gets an explicit, typed "not built yet" response. See `docs/backend/features/dashboard-statistics/README.md` for why (no metric semantics are specified anywhere, and building them would mean inventing business logic).

## Authentication

Bearer JWT (`Authorization: Bearer <token>`) for user-facing endpoints; see `AUTHENTICATION_GUIDE.md`. A separate `x-api-key` header mechanism exists (`AuthGuard.verify_api_key`) but is lightly used in current router wiring.

## Error responses

One shape for every error — see `docs/backend/standards/ERROR_HANDLING.md` for the full contract and error-code registry.

## Known gaps (don't build against these expecting them to exist)

- No API versioning (`/v1`, etc.) anywhere.
- No rate limiting on any endpoint.
- No idempotency-key support on any POST.
- Extension access token has no validation/exchange endpoint — generation only.
