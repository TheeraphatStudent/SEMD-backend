from routers import BaseRoute
from fastapi import UploadFile, HTTPException
from models import PredictionResponse
from typing import Any
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

    async def predict(self, request: Any):
        pass
