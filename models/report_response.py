from pydantic import Field
from models import BaseResponseModel
from typing import Any, List

class ReportResponse(BaseResponseModel):
    data: Any = Field(
        title="data",
        description="Report data"
    )

class ReportListResponse(BaseResponseModel):
    data: List[Any] = Field(
        title="data",
        description="List of reports"
    )
