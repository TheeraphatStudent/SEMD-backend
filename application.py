"""FastAPI application factory.

Extracted from main.py so app construction has no import-time side effects
beyond building the FastAPI instance itself (see SEMD_BACKEND_TARGET_ARCHITECTURE.md
Phase 3 -- application factory item).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from core.error_handlers import register_error_handlers
from core.health import router as health_router
from core.logging import configure_logging
from core.middleware import RequestContextMiddleware
from models import GetDefaultApiEndpoint, GetDefaultHealthCheck
from routers import (
    AccessKeyRoute,
    ApiKeyStatRoute,
    AuthRoute,
    DashboardRoute,
    MLRoute,
    MLTrainingRouter,
    PredictionRoute,
    PredictionStatRoute,
    QueueRoute,
    ReportRoute,
    ReportStatRoute,
    ServiceConfRoute,
    SettingRoute,
    SystemConfigRoute,
    ThirdPartyStatRoute,
    ThirdServiceRoute,
    UrlFlagRoute,
    UrlFlagStatRoute,
    UserRoute,
    UserStatRoute,
)
from routers.report import UsageRoute


def _configure_middleware(app: FastAPI) -> None:
    # Registered after CORSMiddleware so it runs on the outside of the stack
    # (Starlette applies middleware in reverse-registration order) -- every
    # response, including CORS preflight, gets a request ID and access log line.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.add_middleware(RequestContextMiddleware)


def _register_root_endpoints(app: FastAPI) -> None:
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


def _register_routers(app: FastAPI) -> None:
    app.include_router(AuthRoute().get_router())
    app.include_router(UserRoute().get_router())
    app.include_router(MLRoute().get_router())
    app.include_router(MLTrainingRouter().get_router())
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
    app.include_router(health_router)


def create_application() -> FastAPI:
    configure_logging(level='DEBUG' if settings.debug else 'INFO')
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        openapi_url='/openapi.json',
        docs_url='/docs',
        root_path='/api',
        debug=settings.debug
    )
    _configure_middleware(app)
    register_error_handlers(app)
    _register_root_endpoints(app)
    _register_routers(app)
    return app
