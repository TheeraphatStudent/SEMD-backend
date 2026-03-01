from pydantic import BaseModel, Field
from .base_response_model import BaseResponseModel

class MLModelItem(BaseModel):
    model_id: int = Field(
        title = 'Model ID',
        description = 'ID of the model',
        default = 1
    )
    model_name: str = Field(
        title = 'Model Name',
        description = 'Name of the model',
        default = 'SEMD'
    )
    model_version: str | None = Field(
        title = 'Model Version',
        description = 'Version of the model',
        default = 'ML 0.0.1 beta'
    )
    model_description: str | None = Field(
        title = 'Model Description',
        description = 'Description of the model',
        default = None
    )

class MLModelResponse(BaseResponseModel):
    data: list[MLModelItem]