from pydantic import Field
from models import BaseResponseModel
from typing import Any

class MLServiceResponse(BaseResponseModel):
    data: Any = Field(
        title="data",
        description="ML service data"
    )
