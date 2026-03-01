from models import ReportStatResponse, ReportStatListResponse, ReportStatTrendResponse, ReportDetailResponse
from routers import BaseRoute

class ReportStatRoute(BaseRoute):
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

  async def get_report_stat(self):
      pass
  
  async def get_urls_list(self):
      pass

  async def get_urls_trend(self):
      pass
  
  async def get_report_detail(self):
      pass
