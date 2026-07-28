from fastapi import Depends

from core.exceptions import NotImplementedFeatureError
from models.db import User
from guard.auth_guard import AuthGuard
from models import ReportDetailResponse, ReportStatListResponse, ReportStatResponse, ReportStatTrendResponse
from routers import BaseRoute


class ReportStatRoute(BaseRoute):
    """See routers/dashboard/dashboard_route.py's docstring -- same finding
    (unauthenticated `pass` stubs failing response validation on every call),
    same fix (authenticated, honest 501 via NotImplementedFeatureError)."""

    def __init__(self):
        super().__init__(
            prefix="/stat/report",
            tags=["stat-report"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get('', response_model=ReportStatResponse)(self.get_report_stat)
        self.router.get('/list', response_model=ReportStatListResponse)(self.get_urls_list)
        self.router.get('/trend', response_model=ReportStatTrendResponse)(self.get_urls_trend)
        self.router.get('/detail', response_model=ReportDetailResponse)(self.get_report_detail)

    async def get_report_stat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Report statistics are not implemented yet')

    async def get_urls_list(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Report URL list statistics are not implemented yet')

    async def get_urls_trend(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Report trend statistics are not implemented yet')

    async def get_report_detail(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Report detail statistics are not implemented yet')
