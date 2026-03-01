"""FastAPI application with proper project structure.

This application demonstrates:
- Pydantic models with extra JSON schema data
- Modular router organization
- Proper API structure

"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    AuthRoute, MLRoute, PredictionRoute, ReportRoute, DashboardRoute, SettingRoute,
    ReportStatRoute, PredictionStatRoute, UserStatRoute, ApiKeyStatRoute,
    ThirdPartyStatRoute, UrlFlagStatRoute
)
from config.settings import settings
from models import GetDefaultApiEndpoint, GetDefaultHealthCheck
import yaml

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url='/openapi.json',
    docs_url='/docs',
    root_path='/api/v1',
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/', response_model=GetDefaultApiEndpoint)
async def root():
    """Root endpoint with API information."""
    return {
        'message': f"Welcome to {settings.app_name}",
        'version': settings.app_version,
        'docs': '/docs',
        'openapi': '/openapi.json'
    }


@app.get('/health', response_model=GetDefaultHealthCheck)
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'Healthy',
        'cpu_usage': '0%',
        'memory_usage': '0 / 16GB',
        'disk_usage': '0 / 512GB'
    }

# ----------------- Include routers
app.include_router(AuthRoute().get_router())
app.include_router(MLRoute().get_router())
app.include_router(PredictionRoute().get_router())
app.include_router(ReportRoute().get_router())
app.include_router(DashboardRoute().get_router())
app.include_router(SettingRoute().get_router())

app.include_router(ReportStatRoute().get_router())
app.include_router(PredictionStatRoute().get_router())
app.include_router(UserStatRoute().get_router())
app.include_router(ApiKeyStatRoute().get_router())
app.include_router(ThirdPartyStatRoute().get_router())
app.include_router(UrlFlagStatRoute().get_router())

# ----------------- Write document
openapi_yaml = yaml.dump(app.openapi(), sort_keys=False)
with open("openapi.yaml", "w") as f:
    f.write(openapi_yaml)
