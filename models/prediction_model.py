from pydantic import BaseModel, Field
from models import BaseResponseModel
from libs.types import ContextUrlType

class PredictionRequest(BaseModel):
    model_id: int = Field(
        title='Model ID',
        description='ID of the model',
        default=1
    )

    context_urls: ContextUrlType

class PredictionResult(BaseModel):
    url: str
    accurate: float
    type: str
    created_at: int
    predict_id: str

# ------------- Response

class PredictionResponse(BaseResponseModel):
    message: str = Field(
        title="message",
        description="Response message",
        examples=["Predicted successfully!"],
    )

    data: list[PredictionResult] = Field(
        title = 'data',
        description = 'Predict result data',
        examples = [[
            PredictionResult(
                url="https://example.com",
                accurate=98.69,
                type="Benign",
                created_at=1769600369,
                predict_id="PEDT2026012800001"
            )
        ]]
    )
