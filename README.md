# Malicious URL Detection Backend API

A FastAPI-based backend service for malicious URL detection with enhanced schema validation.

## Project Structure

```text
semd-backend/
├── main.py                 # FastAPI application entry point
├── application.py          # Application factory/bootstrap
├── config/                 # Runtime configuration and examples
├── core/                   # Cross-cutting app concerns
├── control/                # Use-case orchestration layer
├── docker/                 # Compose, Dockerfiles, DB bootstrap SQL
├── docs/backend/           # Backend architecture and feature docs
├── guard/                  # Auth dependencies and DB session providers
├── models/                 # Pydantic models plus SQLAlchemy ORM in models/db/
├── routers/                # API route handlers
├── services/               # Domain services and integrations
├── tests/unit/             # Unittest suite
├── workers/                # Redis/ML background workers
├── requirements.txt
├── makefile
└── README.md
```

## Setup Project

Requires [`uv`](https://docs.astral.sh/uv/) and `make`.

```bash
make setup
```

This will:

1. Copy `config/backend.example.ini` → `config/backend.ini` and `config/redis.example.conf` → `config/redis.conf` (won't overwrite existing files)
2. Extract Postgres/Redis credentials from `backend.ini`, patch `config/redis.conf`, and generate `docker/postgres.env`
3. Install Python dependencies via `uv add -r requirements.txt` + `uv sync`

## Configuration

`config/settings.py` resolves every setting as **environment variable -> `config/backend.ini` -> built-in
default**. For Redis specifically: `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB` set in the
process environment (e.g. a container's `environment:` block) override `backend.ini`'s `[REDIS]` section.
A *blank* env var (present but empty, e.g. an unresolved `${VAR}` in compose) does not erase a valid
`backend.ini` value — it's treated as absent (`env_ignore_empty=True`).

This matters for containers: `backend.ini`'s `HOST = 127.0.0.1` only works for local (non-container) runs,
where the backend and Redis share the host network. Inside `docker/compose.yaml`/Podman, set
`REDIS_HOST` (and, if it differs from `backend.ini`, `REDIS_PASSWORD`/`REDIS_PORT`/`REDIS_DB`) to the
shared Redis's container/service name so the backend can reach the same authenticated Redis instance the
`semd-ml` worker consumes from.

## Docker Layout

All runtime/container assets now live under `docker/`:

- `docker/compose.yaml` — backend + PostgreSQL + Redis stack
- `docker/backend.Dockerfile` — backend image
- `docker/redis.Dockerfile` — Redis image with `config/redis.conf`
- `docker/postgres/init.sql` — database bootstrap SQL
- `docker/postgres.env` — generated Postgres container environment file

The SQLAlchemy ORM layer now lives under `models/db/`, while the rest of `models/` remains the Pydantic request/response package.

## Running the Application

After setup:

```bash
make start
```

The API will be available at:

- **API**: http://127.0.0.1:8000
- **Documentation**: http://127.0.0.1:8000/docs
- **Alternative Docs**: http://127.0.0.1:8000/redoc

---

Production mode:

```bash
make prod
```

Run the ML result Redis worker:

```bash
make worker
```

See `make help` for the full list of targets.

## Added third service

### Cloudflare
POST http://localhost:8000/setting/third-service/

```json
{
  "service_name": "Cloudflare Radar - URL Scanner",
  "base_url": "https://api.cloudflare.com/client/v4/accounts/{{account_id}}/urlscanner/v2/scan",
  "http_method": "POST",
  "headers_json": {
    "Content-Type": "application/json",
    "Authorization": "Bearer ejy.example"
    },
  "config_json": {
    "body_template": [{"key": "url", "input": "url"}],
    "url_template": {
      "path_params": {"account_id": "5186xxxxxxxxxxxxxxxxxxx"}
    },
    "response_mapping": {
      "is_malicious": "result.malicious"
    }
  }
}
```

### Thai phishtank
POST http://localhost:8000/setting/third-service/

```json
{
  "service_name": "Thai PhishTank - Phishing URL Check",
  "base_url": "https://thaiphishtank.org/api/phishing-url&url={{url}}&api_key={{api_key}}",
  "http_method": "GET",
  "secret_hash": "",
  "headers_json": {},
  "config_json": {}
}
```

## Ml Service

```flow
SEMD-backend (FastAPI) 
    → ml_prediction_service.py 
    → ml_service_client.py (submits job to Redis queue)
    → Redis (ml_prediction_queue)
    → SEMD-ml Docker container (queue_worker)
    → prediction_service.py (uses ml_pipeline)
    → Redis cache (ml_result:{job_id})
    → ml_service_client.py (polls for result)
    → Response to client
```

## Resource

- [2fa-qa](https://stefansundin.github.io/2fa-qr/)
- [FastAPI](https://fastapi.tiangolo.com/#run-it)
