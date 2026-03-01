from routers import BaseRoute
from models import PredictionRequest, PredictionResponse
from fastapi import UploadFile, HTTPException
import csv
import io

class PredictionRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/prediction",
            tags=["prediction"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.post("", response_model=PredictionResponse)(self.predict)

    async def predict(self, request: PredictionRequest):
        pass
