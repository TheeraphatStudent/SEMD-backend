from models import ApiKeyStatResponse, ApiKeyUsageResponse, ApiKeyTrendResponse, ApiEndpointStatResponse
from routers import BaseRoute

class ApiKeyStatRoute(BaseRoute):
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

  async def get_api_key_stat(self):
      pass
  
  async def get_api_key_usage(self):
      pass
  
  async def get_api_key_trend(self):
      pass
  
  async def get_api_endpoint_stat(self):
      pass
