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
├── .env.example            # Environment variables template
├── backend-working.sh      # Virtual environment activation script
└── README.md
```

## Setup Project

```bash
source ./backend-working.sh
```

This will:

1. Deactivate any existing virtual environment
2. Fix permissions for the `.venv` directory
3. Activate the backend virtual environment
4. Install/update requirements
5. Display installed packages

### To deactivate

```bash
deactivate
```

## Running the Application

After setup:

```bash
fastapi dev main.py
```

The API will be available at:

- **API**: http://127.0.0.1:8000
- **Documentation**: http://127.0.0.1:8000/docs
- **Alternative Docs**: http://127.0.0.1:8000/redoc

---

Running with uvicorn 

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Working with wsl or linux

**Fix ascii problem**

Problem:
```bash
-bash: $'\r': command not found
-bash: ./model-working.sh: line 25: syntax error: unexpected end of file
```

Fixed:
```bash
sed -i 's/\r$//' ./backend-working.sh
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

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
  "base_url": "https://thaiphishtank.org/api/phishing-url",
  "http_method": "GET",
  "secret_hash": "",
  "headers_json": {},
  "config_json": {
    "body_template": [],
    "url_template": {
      "query_params": {
        "url": "url",
        "api_key": "thai_phishtank_api_key"
      }
    },
    "response_mapping": {
      "is_phishing": "data.is_phishing",
      "confidence": "data.confidence"
    }
  }
}
```

## Resource

- [2fa-qa](https://stefansundin.github.io/2fa-qr/)
- [FastAPI](https://fastapi.tiangolo.com/#run-it)