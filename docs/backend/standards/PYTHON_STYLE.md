# Python Style Standard

## Tooling

`ruff` for lint + import sorting, `mypy` for type checking — both added in Phase 3 (`pyproject.toml`, `make lint`/`make typecheck`/`make check`). No formatter (black/ruff-format) adopted — line length is not enforced (`E501` ignored deliberately in `pyproject.toml`, since imposing a repo-wide reformat on ~150 pre-existing files was judged not worth the diff noise for this pass; revisit if the team wants it).

**One documented footgun**: `ruff check --fix` will alphabetize `routers/__init__.py`'s imports, which breaks a load-bearing circular-import order (`.base_route` must import before `.auth`, since `routers/auth/auth_route.py` reaches back into the partially-initialized `routers` package for `BaseRoute`). This bit the Domain 10 pass directly — caught by the test suite, fixed, and pinned with a `# noqa: I001` plus an explanatory comment in that file. Re-verify import order in that specific file after any repo-wide `--fix` run.

## Layering (see `SEMD_BACKEND_TARGET_ARCHITECTURE.md` for the full rationale)

`routers/ -> control/ -> services/ -> database/`, with `models/` (Pydantic schemas) used across layers and `core/` (added Phase 3) for cross-cutting concerns (config, logging, security, middleware, exceptions, error handlers, health). Routers own HTTP concerns only; as of the Domain 2-13 sweep, no router in an audited domain contains business logic beyond request/response shaping and (where relevant) admin-role gating via `Depends(AuthGuard.require_admin)`.

## Naming

- `RoleType`, `FlagType`, `ACLType`, `ReportStatusType`, `UsageLogType`, `ServiceType`, `ModelStageType`, `OAuthProviderType` — all string enums in `libs/types/enums.py`, checked before adding any new status/type string anywhere.
- Domain files follow `<domain>_route.py` / `<domain>_control.py` / `<domain>_service.py` / `<domain>_model.py` (+ `_request.py`/`_response.py`) consistently.
- Snake_case for functions/variables, PascalCase for classes — standard, no violations found worth flagging.

## Comments and docstrings

Default to none. Where present in code touched during this refactor, comments explain **why**, not what — a hidden constraint, a workaround, or the reasoning behind a non-obvious decision (e.g. `guard/auth_guard.py`'s comment on why `get_current_user`/`require_admin` must be module-level functions assigned as `staticmethod(...)`, not `@staticmethod def` inside the class body — a real bug this pass hit and fixed, not decoration). Pre-existing docstrings in untouched code are left as-is, not retrofitted.

## Type hints

See `TYPE_SAFETY.md` for the systemic gap (SQLAlchemy `Column[T]` vs. Python `T`) and the baseline mypy count. New code written during this refactor (`core/*.py`, all router permission/error-handling changes) is fully typed and mypy-clean; pre-existing code is not retrofitted wholesale, only where directly touched.

## What's not enforced

No pre-commit hooks, no CI (confirmed absent in Phase 1 audit — no `.github/workflows/`). `make check` (test + typecheck + lint) exists as a manual gate; nothing runs it automatically yet.
