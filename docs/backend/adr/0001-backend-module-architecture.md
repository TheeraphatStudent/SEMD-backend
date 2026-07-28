# ADR 0001: Keep existing per-domain flat layout; add a `core/` package

## Status
Accepted

## Context
The refactoring mandate's example target tree proposes `app/modules/<domain>/{router,schemas,service,repository,models,dependencies,permissions,exceptions,tests}/`. The current-state audit (`SEMD_BACKEND_CURRENT_STATE.md`) found the existing codebase already splits by domain — one file per domain in each of `routers/`, `control/`, `services/`, `models/` — with a mostly-honored `routers -> control -> services -> database` dependency direction. The one real dependency-direction violation found is `control/`/`services/` raising `fastapi.HTTPException` directly instead of typed domain exceptions; that is a coupling problem independent of directory layout.

## Decision
Keep the existing top-level layout (`routers/`, `control/`, `services/`, `models/`, `database/`, `guard/`, `libs/`, `workers/`). Add a new `core/` package for cross-cutting concerns not currently owned by any layer: config, logging, security (SSRF/URL validation), middleware, typed exceptions, error handlers, health checks.

## Alternatives rejected
- **Full migration to `app/modules/<domain>/` folder-per-feature.** Rejected: would require moving ~150 files with no behavioral change, violates the mandate's own "avoid unnecessary abstraction" and "do not combine large file moves with behavior changes" rules, and the domain boundaries it targets already exist in the current layout (as parallel same-named files across folders rather than folders-per-domain). No concrete pain point in the current codebase (file size, merge conflicts, onboarding confusion) was found that this reorg would solve.
- **Introduce a formal repository-`Protocol` layer for every domain.** Rejected as a global mandate; `services/*_service.py` already plays this role for most domains. Left as a per-feature decision for Phase 4 where a service genuinely mixes DB and third-party I/O.

## Consequences
- Lower migration risk and smaller diffs per Phase 4 feature, since no file is force-moved.
- The mandate's example tree's benefits (isolating a domain's tests, DI, permissions in one folder) are only partially realized — a future reorg remains possible if a specific domain later needs it (see target architecture doc §5).
