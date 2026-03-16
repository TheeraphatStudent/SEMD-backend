from models import (
    SystemStatResponse, SystemHealthResponse, SystemPerformanceResponse,
    ThirdPartyStatResponse, UrlFlagStatResponse, ReportStatResponse,
    ApiKeyStatResponse, UserStatResponse
)
from routers import BaseRoute

class DashboardRoute(BaseRoute):
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


    def getSystemStat(self):
        pass
    
    def getSystemHealth(self):
        pass
    
    def getSystemPerformance(self):
        pass

    def getThirdPartyStat(self):
        pass

    def getUrlFlagStat(self):
        pass

    def getUrlReportStat(self):
        pass

    def getApiAccessKeyStat(self):
        pass

    def getUserStat(self):
        pass
