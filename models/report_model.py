from pydantic import BaseModel, Field
from libs.types import ContextUrlType

class ReportModelItem(BaseModel):
    id: str
    url: str
    type: str
    verify_status: str
    created_at: int
    report_by: dict = Field(
        title="Report by",
        description="User who reported the URL",
        examples=[{
            "id": 1,
            "img_url": "https://example.com/img.jpg",
            "username": "th33raphat"
        }]
    )

class ReportModelResponse(BaseModel):
    message: str
    data: list[ReportModelItem]

class ReportModelRequest(BaseModel):
    type: str
    context_urls: ContextUrlType