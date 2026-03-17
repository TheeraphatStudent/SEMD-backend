"""FastAPI application with proper project structure.

This application demonstrates:
- Pydantic models with extra JSON schema data
- Modular router organization
- Proper API structure

"""

import sys
import argparse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    AuthRoute, UserRoute, MLRoute, PredictionRoute, ReportRoute, DashboardRoute, SettingRoute,
    ThirdServiceRoute, ServiceConfRoute, UrlFlagRoute, AccessKeyRoute, SystemConfigRoute, QueueRoute,
    ReportStatRoute, PredictionStatRoute, UserStatRoute, ApiKeyStatRoute, ThirdPartyStatRoute, UrlFlagStatRoute
)
from routers.report import UsageRoute
from config.settings import settings
from models import GetDefaultApiEndpoint, GetDefaultHealthCheck
import yaml

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url='/openapi.json',
    docs_url='/docs',
    root_path='/api',
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    # allow_credentials=True,
    allow_credentials=False,
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
app.include_router(UserRoute().get_router())
app.include_router(MLRoute().get_router())
app.include_router(PredictionRoute().get_router())
app.include_router(ReportRoute().get_router())
app.include_router(DashboardRoute().get_router())
app.include_router(SettingRoute().get_router())
app.include_router(ThirdServiceRoute().get_router())
app.include_router(ServiceConfRoute().get_router())
app.include_router(UrlFlagRoute().get_router())
app.include_router(AccessKeyRoute().get_router())
app.include_router(SystemConfigRoute().get_router())
app.include_router(QueueRoute().get_router())

app.include_router(ReportStatRoute().get_router())
app.include_router(PredictionStatRoute().get_router())
app.include_router(UserStatRoute().get_router())
app.include_router(ApiKeyStatRoute().get_router())
app.include_router(ThirdPartyStatRoute().get_router())
app.include_router(UrlFlagStatRoute().get_router())
app.include_router(UsageRoute().get_router())

# ----------------- Write document
openapi_yaml = yaml.dump(app.openapi(), sort_keys=False)
with open("openapi.yaml", "w") as f:
    f.write(openapi_yaml)


def main():
    """CLI entry point for running the FastAPI application."""
    parser = argparse.ArgumentParser(description='FastAPI Application CLI')
    parser.add_argument(
        'command',
        choices=['dev', 'prod'],
        help='Command to run: dev (development with auto-reload) or prod (production with uvicorn)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind (default: 8000)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'dev':
        import uvicorn
        print(f"🚀 Starting FastAPI in DEVELOPMENT mode on {args.host}:{args.port}")
        print(f"📝 Auto-reload enabled - watching for file changes")
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info"
        )
    elif args.command == 'prod':
        import uvicorn
        print(f"🚀 Starting FastAPI in PRODUCTION mode on {args.host}:{args.port}")
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=False,
            workers=4,
            log_level="warning"
        )


if __name__ == "__main__":
    main()
