from models import ThirdPartyStatResponse, ThirdPartyServiceResponse, ThirdPartyTrendResponse, ThirdPartyErrorResponse
from routers import BaseRoute

class ThirdPartyStatRoute(BaseRoute):
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

  async def get_third_party_stat(self):
      pass
  
  async def get_third_party_services(self):
      pass
  
  async def get_third_party_trend(self):
      pass
  
  async def get_third_party_errors(self):
      pass
