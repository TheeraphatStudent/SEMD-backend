from fastapi import Depends

from core.exceptions import NotImplementedFeatureError
from models.db import User
from guard.auth_guard import AuthGuard
from models import UrlFlagCategoryResponse, UrlFlagDetailResponse, UrlFlagStatResponse, UrlFlagTrendResponse
from routers import BaseRoute


class UrlFlagStatRoute(BaseRoute):
    """See routers/dashboard/dashboard_route.py's docstring -- same finding
    (unauthenticated `pass` stubs failing response validation on every call),
    same fix (authenticated, honest 501 via NotImplementedFeatureError)."""

    def __init__(self):
        super().__init__(
            prefix="/stat/url-flag",
            tags=["stat-url-flag"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get('', response_model=UrlFlagStatResponse)(self.get_url_flag_stat)
        self.router.get('/trend', response_model=UrlFlagTrendResponse)(self.get_url_flag_trend)
        self.router.get('/detail', response_model=UrlFlagDetailResponse)(self.get_url_flag_detail)
        self.router.get('/category', response_model=UrlFlagCategoryResponse)(self.get_url_flag_category)

    async def get_url_flag_stat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('URL flag statistics are not implemented yet')

    async def get_url_flag_trend(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('URL flag trend statistics are not implemented yet')

    async def get_url_flag_detail(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('URL flag detail statistics are not implemented yet')

    async def get_url_flag_category(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('URL flag category statistics are not implemented yet')
