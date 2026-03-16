from models import UrlFlagStatResponse, UrlFlagTrendResponse, UrlFlagDetailResponse, UrlFlagCategoryResponse
from routers import BaseRoute

class UrlFlagStatRoute(BaseRoute):
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

  async def get_url_flag_stat(self):
      pass
  
  async def get_url_flag_trend(self):
      pass
  
  async def get_url_flag_detail(self):
      pass
  
  async def get_url_flag_category(self):
      pass
