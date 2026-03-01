from models import PredictionStatResponse, PredictionTrendResponse, PredictionByModelResponse, PredictionDetailResponse
from routers import BaseRoute

class PredictionStatRoute(BaseRoute):
  def __init__(self):
        super().__init__(
            prefix="/stat/prediction",
            tags=["stat-prediction"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get('', response_model=PredictionStatResponse)(self.get_prediction_stat)
        self.router.get('/trend', response_model=PredictionTrendResponse)(self.get_prediction_trend)
        self.router.get('/by-model', response_model=PredictionByModelResponse)(self.get_prediction_by_model)
        self.router.get('/detail', response_model=PredictionDetailResponse)(self.get_prediction_detail)

  async def get_prediction_stat(self):
      pass
  
  async def get_prediction_trend(self):
      pass
  
  async def get_prediction_by_model(self):
      pass
  
  async def get_prediction_detail(self):
      pass
