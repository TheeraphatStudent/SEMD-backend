from pydantic import Field
from models import BaseResponseModel
from typing import Any


class PredictionResponse(BaseResponseModel):
    data: Any = Field(
        title='data',
        description='Prediction result data'
    )


class PredictionDetailResponse(BaseResponseModel):
    data: Any = Field(
        title='data',
        description='Prediction detail data'
    )
