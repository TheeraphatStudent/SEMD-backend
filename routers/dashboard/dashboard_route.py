from fastapi import Depends

from core.exceptions import NotImplementedFeatureError
from models.db import User
from guard.auth_guard import AuthGuard
from models import (
    ApiKeyStatResponse,
    ReportStatResponse,
    SystemHealthResponse,
    SystemPerformanceResponse,
    SystemStatResponse,
    ThirdPartyStatResponse,
    UrlFlagStatResponse,
    UserStatResponse,
)
from routers import BaseRoute


class DashboardRoute(BaseRoute):
    """All 8 endpoints below were previously unauthenticated `pass` stubs
    that returned `None` against a declared `response_model`, which FastAPI
    turns into a 500 response-validation failure on every call -- i.e. every
    one of these was already unusable, just not honestly so. Now:
    (1) authenticated like every other domain in this backend, and
    (2) raise NotImplementedFeatureError (501, matching the router's own
    long-declared `501: {"description": "Not implemented"}` response) instead
    of silently failing response validation. Building the actual dashboard
    aggregation logic needs product-defined metric semantics (what counts as
    a "system performance" figure? which time window? aggregated how?) that
    don't exist anywhere in this codebase or its docs -- not invented here,
    per the mandate's prohibition on fabricating requirements. See
    docs/backend/features/dashboard-statistics/README.md.
    """

    def __init__(self):
        super().__init__(
            prefix="/dashboard",
            tags=["Dashboard"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get('/system-stat', response_model=SystemStatResponse)(self.getSystemStat)
        self.router.get('/system-health', response_model=SystemHealthResponse)(self.getSystemHealth)
        self.router.get('/system-performance', response_model=SystemPerformanceResponse)(self.getSystemPerformance)
        self.router.get('/third-party-stat', response_model=ThirdPartyStatResponse)(self.getThirdPartyStat)
        self.router.get('/url-flag-stat', response_model=UrlFlagStatResponse)(self.getUrlFlagStat)
        self.router.get('/url-report-stat', response_model=ReportStatResponse)(self.getUrlReportStat)
        self.router.get('/api-access-key-stat', response_model=ApiKeyStatResponse)(self.getApiAccessKeyStat)
        self.router.get('/user-stat', response_model=UserStatResponse)(self.getUserStat)

    async def getSystemStat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('System statistics are not implemented yet')

    async def getSystemHealth(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('System health statistics are not implemented yet')

    async def getSystemPerformance(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('System performance statistics are not implemented yet')

    async def getThirdPartyStat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Third-party service statistics are not implemented yet')

    async def getUrlFlagStat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('URL flag statistics are not implemented yet')

    async def getUrlReportStat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('URL report statistics are not implemented yet')

    async def getApiAccessKeyStat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('API access key statistics are not implemented yet')

    async def getUserStat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('User statistics are not implemented yet')
