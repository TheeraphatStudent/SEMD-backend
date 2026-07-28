# Database Documentation

## Engine and bootstrap

**PostgreSQL** — confirmed via `psycopg2-binary`/`asyncpg` drivers and `docker/compose.yaml` (`postgres:latest` image), not inferred from documentation (per the mandate's explicit instruction not to assume the engine from docs alone).

**No migration tool** (no Alembic, no versioned migration files). Schema is bootstrapped from `docker/postgres/init.sql` — a raw DDL script mounted as a Postgres container init script — with `PostgresClient.init_db()`'s `Base.metadata.create_all(bind=self.engine)` as a fallback for any table `init.sql` doesn't cover. See `migration-guide.md` for what this means in practice and a recommendation.

## Structural finding, fixed in Phase 3

`database/models.py` (the SQLAlchemy ORM layer the application actually queries through) declared **zero** `ForeignKey()`s across all 13 tables, while `docker/postgres/init.sql` (the DDL that actually creates the schema) declares real `REFERENCES ... ON DELETE {CASCADE|SET NULL}` constraints on nearly every foreign-key-shaped column. The database was always enforcing referential integrity; the ORM model just didn't know about it, so every join in application code was a manual `.join(Model, Model.fk_col == Other.fk_col)` instead of a `relationship()`-backed join, with no static or runtime protection against a column rename drifting the two out of sync. **Fixed**: `ForeignKey()` added to every column matching `init.sql`'s declared constraint, including matching `ondelete` behavior exactly. One genuine DDL bug found in the process and preserved (not silently "fixed"): `url_reported.user_id` is declared both `ON DELETE SET NULL` and `NOT NULL` in `init.sql` — contradictory; deleting a referenced user would violate the `NOT NULL` constraint at the DB level. Flagged in `table-dictionary.md` and in code, not resolved (resolving it means picking a side — nullable-and-cascade-to-null, or non-nullable-and-cascade-delete-the-audit-row — a product decision about what should happen to a report's audit trail when its actor is deleted).

`relationship()` (SQLAlchemy's ORM-level join helper, distinct from `ForeignKey()`) was **not** added — per the target architecture decision, only where a repository genuinely needs eager/joined loading, evaluated per-domain, to avoid loading unnecessary joins into every query.

## Contents

- `er-diagram.md` — entity-relationship diagram, as-implemented
- `table-dictionary.md` — full column-level dictionary for all 13 tables
- `indexes.md` — what's indexed (PK/UNIQUE only), what query patterns exist with no index support, and why none were speculatively added
- `migration-guide.md` — how schema changes are made today, and a recommendation
- `transaction-boundaries.md` — session/commit patterns observed across the codebase
