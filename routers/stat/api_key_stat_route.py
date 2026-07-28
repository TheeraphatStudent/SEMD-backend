from fastapi import Depends

from core.exceptions import NotImplementedFeatureError
from models.db import User
from guard.auth_guard import AuthGuard
from models import ApiEndpointStatResponse, ApiKeyStatResponse, ApiKeyTrendResponse, ApiKeyUsageResponse
from routers import BaseRoute


class ApiKeyStatRoute(BaseRoute):
    """See routers/dashboard/dashboard_route.py's docstring -- same finding
    (unauthenticated `pass` stubs failing response validation on every call),
    same fix (authenticated, honest 501 via NotImplementedFeatureError)."""

    def __init__(self):
        super().__init__(
            prefix="/stat/api-key",
            tags=["stat-api-key"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get('', response_model=ApiKeyStatResponse)(self.get_api_key_stat)
        self.router.get('/usage', response_model=ApiKeyUsageResponse)(self.get_api_key_usage)
        self.router.get('/trend', response_model=ApiKeyTrendResponse)(self.get_api_key_trend)
        self.router.get('/endpoint', response_model=ApiEndpointStatResponse)(self.get_api_endpoint_stat)

    async def get_api_key_stat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('API key statistics are not implemented yet')

    async def get_api_key_usage(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('API key usage statistics are not implemented yet')

    async def get_api_key_trend(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('API key trend statistics are not implemented yet')

    async def get_api_endpoint_stat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('API endpoint statistics are not implemented yet')
