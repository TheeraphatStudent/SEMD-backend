from fastapi import Depends

from core.exceptions import NotImplementedFeatureError
from models.db import User
from guard.auth_guard import AuthGuard
from models import PredictionByModelResponse, PredictionDetailResponse, PredictionStatResponse, PredictionTrendResponse
from routers import BaseRoute


class PredictionStatRoute(BaseRoute):
    """See routers/dashboard/dashboard_route.py's docstring -- same finding
    (unauthenticated `pass` stubs failing response validation on every call),
    same fix (authenticated, honest 501 via NotImplementedFeatureError)."""

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

    async def get_prediction_stat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Prediction statistics are not implemented yet')

    async def get_prediction_trend(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Prediction trend statistics are not implemented yet')

    async def get_prediction_by_model(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Prediction-by-model statistics are not implemented yet')

    async def get_prediction_detail(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Prediction detail statistics are not implemented yet')
