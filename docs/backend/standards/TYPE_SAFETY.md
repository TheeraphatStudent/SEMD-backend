# Type Safety Standard

## Baseline (honest, not aspirational)

As of this document: `make typecheck` → **188 mypy errors in 33 files** (153 source files checked); `make lint` → **141 ruff errors** (128 auto-fixable). Neither tool existed before Phase 3 of this refactor — this is a first-ever baseline, not a regression from some prior clean state. Per the mandate's own rule ("do not hide failed validation commands"), every domain checkpoint in this refactor reports these counts and confirms whether the domain's own changes added to them (they didn't, in every domain audited — verified per-file after each change, not just at the end).

## The one dominant, systemic finding: `Column[T]` vs `T`

The overwhelming majority of the 188 mypy errors are one repeated shape: a SQLAlchemy ORM attribute (typed by mypy as `Column[int]`, `Column[str]`, `Column[datetime]`, etc.) passed into a function or Pydantic model expecting the plain Python type (`int`, `str`, `datetime`). Example, one of dozens:

```
routers/ml/ml_route.py:249: error: Argument 2 to "ModelRegistryControl" has incompatible type "Column[int]"; expected "int"
```

This is because `database/models.py` uses the legacy `Column(...)` declarative style rather than SQLAlchemy 2.0's `Mapped[int]`/`mapped_column()` typed style. At runtime a `Column[int]` attribute on an ORM instance actually **is** a plain `int` — mypy's static view (informed by SQLAlchemy's own stub types) doesn't know that. **This is a static-analysis-only issue, not a runtime bug** — every one of these call sites has been working correctly in production; mypy is correctly flagging an ergonomic gap, not a defect.

**Not fixed in this pass**: migrating `database/models.py` to `Mapped[...]`/`mapped_column()` would resolve the entire category in one file, but it's a mechanical, repo-wide-blast-radius change (every ORM attribute access, everywhere) that's higher-risk to do quickly than the value of silencing ~150 mypy findings justifies mid-refactor. Recommended as a dedicated follow-up, not bundled here — see `SEMD_BACKEND_REFACTOR_ROADMAP.md`.

## Rules (for new code)

1. All public functions have parameter and return types.
2. Avoid `Any` except at genuinely dynamic external boundaries (third-party JSON response mapping in `services/client/third_service_executor.py` is the one legitimate use found and kept; `Any` fields that leaked into **public API response schemas** — `models/user_model.py`'s secret fields — were removed in Domain 4, not because of typing hygiene but because they shouldn't have been there at all).
3. Use Pydantic models for every request/response contract — no bare dict responses except where a third-party payload is genuinely dynamic (`Dict[str, Any]` on `/setting/third-service/{id}/execute`'s response, matching the arbitrary shape of whatever the configured vendor returns).
4. Use the `libs/types/enums.py` enums for status/role/type strings — never a bare string literal comparison. Two `ACLType`/`ServiceType` fields are backed by real Postgres `ENUM` columns; the rest are app-level only (a pre-existing gap, not addressed here — see `SEMD_BACKEND_CURRENT_STATE.md` section 9.2).
5. `core/exceptions.py`'s `AppError` hierarchy is fully typed; new business errors should subclass it with explicit `status`/`code` class attributes, not bare tuples or dicts.
6. **Every `# type: ignore` must include a reason.** One exists in this codebase, added deliberately: `core/error_handlers.py::register_error_handlers`, three `# type: ignore[arg-type]` lines with a comment explaining that Starlette's `add_exception_handler` stub is invariant on the exception parameter type, which is FastAPI's own documented registration pattern. No blanket/global mypy or ruff suppressions exist anywhere.

## Known specific gaps beyond the systemic one

- `services/prediction_service.py:20`: `def __init__(self, db: AsyncSession = None)` — implicit-optional, flagged by mypy (`no_implicit_optional=True` is mypy's modern default). Not fixed — pre-existing, low-risk, not touched by any domain's actual changes.
- A handful of `E712` ruff findings (`== True` instead of truthy check) in SQLAlchemy `.where()` clauses (`services/prediction_service.py`, `control/prediction_control.py`) — left as-is since `Column == True` and bare `Column` can generate different SQL in some SQLAlchemy versions/configurations; not risk-free to auto-fix without verifying against the actual Postgres behavior, so left as documented baseline noise rather than blindly changed.
