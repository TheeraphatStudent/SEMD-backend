# Migration Guide

## How schema changes happen today

There is no migration tool. `docker/postgres/init.sql` is a raw DDL script, mounted as a Postgres container init script via `docker/compose.yaml` — it runs once, when the Postgres container's data directory is first initialized. `services/client/postgres_client.py::PostgresClient.init_db()` calls `Base.metadata.create_all(bind=self.engine)` as a fallback, which creates any table `init.sql` doesn't cover (or if invoked against a fresh, non-Docker Postgres instance).

**Practical consequence**: there is no reproducible, versioned path from "empty database" to "current schema" that also captures every incremental change made after initial creation. A change to `init.sql` doesn't retroactively apply to an already-running database — it only takes effect for a brand-new container/data directory. Anyone who needs to apply a schema change to an existing database today has to do it by hand (a manual `ALTER TABLE`, or dropping and recreating).

## What this means for the changes made in this refactor

The Phase 3 `ForeignKey()` additions to `database/models.py` **did not change the database schema** — the constraints they declare already existed in `docker/postgres/init.sql`'s DDL (confirmed column-by-column before adding each one, see `table-dictionary.md`). This was purely making the ORM model accurately reflect what the database already enforces; no migration was needed or performed.

No domain in this refactor's Phase 4 sweep required an actual schema change (new column, new table, altered constraint) — every fix was either an authorization/error-handling code change or a data-interpretation change (e.g. hashing the extension token uses the same `Text` column, just storing a different value in it).

## Recommendation for future schema changes

Adopt Alembic (the standard SQLAlchemy migration tool) before the next schema change that isn't purely additive-and-optional. Concretely:

1. `alembic init` against the existing `database/models.py` metadata.
2. Generate an initial migration that matches the current live schema exactly (`alembic revision --autogenerate`, then hand-verify against `docker/postgres/init.sql` since they must match column-for-column before trusting autogenerate for anything after).
3. Retire `docker/postgres/init.sql`'s role as the source of truth — keep it only as a historical reference or replace the Docker init-script step with `alembic upgrade head` on container start.
4. This is a deployment-model decision (does the team want migrations to run automatically on deploy, or as a manual gated step?) that should be confirmed with whoever owns production deployment before adopting — not decided unilaterally in this refactor.

## Rollback notes for this refactor's changes

No migration exists to roll back — see above, no schema was changed. Code-level rollback for any domain's changes is `git checkout -- <files>`, documented per-domain in each `docs/backend/features/<domain>/README.md`.
