# Docker Layout

All container/runtime assets for `semd-backend` now live in this directory.

## Files

- `compose.yaml` — single stack entrypoint for backend, PostgreSQL, and Redis
- `backend.Dockerfile` — FastAPI backend image
- `redis.Dockerfile` — Redis image that loads `config/redis.conf`
- `postgres/init.sql` — PostgreSQL bootstrap schema/data
- `postgres.env` — generated Postgres environment file from `make config`

## Common commands

Start the full stack:

```bash
podman compose -f docker/compose.yaml up -d --build
```

Stop the full stack:

```bash
podman compose -f docker/compose.yaml down
```

Open PostgreSQL:

```bash
podman exec -it semd-database psql -U <username> -d <database name>
```

Open Redis:

```bash
podman exec -it semd-redis redis-cli
```
