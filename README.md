# Malicious URL Detection Backend API

A FastAPI-based backend service for malicious URL detection with enhanced schema validation.

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config/                 # Application configuration package
│   └── settings.py         # Pydantic settings definition
│
├── db/                     # Database configuration
│
├── guard/                  # Check auth from user request routing 
│
├── models/                 # Pydantic models and configuration helpers
│   ├── items.py            # Item data models with schema validation
│   └── users.py            # User data models with schema validation
│
├── routers/                # API route handlers
│   ├── items.py            # Item management endpoints
│   └── users.py            # User management endpoints
│
├── service/                # Logic
│   └── external_service/   # Connect to exernal api
│
├── workers/                # Ai & Redis worker
├── requirements.txt        # Python dependencies
├── makefile                # setup/start/prod/worker helper commands (uv-based)
└── README.md
```

## Setup Project

Requires [`uv`](https://docs.astral.sh/uv/) and `make`.

```bash
make setup
```

This will:

1. Copy `config/backend.example.ini` → `config/backend.ini` and `config/redis.example.conf` → `config/redis.conf` (won't overwrite existing files)
2. Extract Postgres/Redis credentials from `backend.ini` and patch `config/redis.conf`, generate `database/.env`, and patch `database/docker-compose.database.yaml`
3. Install Python dependencies via `uv add -r requirements.txt` + `uv sync`

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