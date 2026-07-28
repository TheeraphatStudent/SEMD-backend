from fastapi import Depends

from core.exceptions import NotImplementedFeatureError
from models.db import User
from guard.auth_guard import AuthGuard
from models import ThirdPartyErrorResponse, ThirdPartyServiceResponse, ThirdPartyStatResponse, ThirdPartyTrendResponse
from routers import BaseRoute


class ThirdPartyStatRoute(BaseRoute):
    """See routers/dashboard/dashboard_route.py's docstring -- same finding
    (unauthenticated `pass` stubs failing response validation on every call),
    same fix (authenticated, honest 501 via NotImplementedFeatureError)."""

    def __init__(self):
        super().__init__(
            prefix="/stat/third-party",
            tags=["stat-third-party"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get('', response_model=ThirdPartyStatResponse)(self.get_third_party_stat)
        self.router.get('/services', response_model=ThirdPartyServiceResponse)(self.get_third_party_services)
        self.router.get('/trend', response_model=ThirdPartyTrendResponse)(self.get_third_party_trend)
        self.router.get('/errors', response_model=ThirdPartyErrorResponse)(self.get_third_party_errors)

    async def get_third_party_stat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Third-party statistics are not implemented yet')

    async def get_third_party_services(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Third-party service statistics are not implemented yet')

    async def get_third_party_trend(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Third-party trend statistics are not implemented yet')

    async def get_third_party_errors(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Third-party error statistics are not implemented yet')
