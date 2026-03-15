from pydantic import BaseModel, Field
from typing import Optional
from libs.types.enums import FlagType, ReportStatusType


class UrlReportCreateRequest(BaseModel):
    url: str = Field(..., description="URL to report")
    categories: FlagType = Field(FlagType.BENIGN, description="Category of the URL (MALICIOUS or BENIGN)")
    status: ReportStatusType = Field(ReportStatusType.PENDING, description="Status of the report")
    remark: Optional[str] = Field(None, max_length=256, description="Additional remark")


class UrlReportUpdateRequest(BaseModel):
    url: Optional[str] = Field(None, description="URL to report")
    categories: Optional[FlagType] = Field(None, description="Category of the URL (MALICIOUS or BENIGN)")
    status: Optional[ReportStatusType] = Field(None, description="Status of the report")
    remark: Optional[str] = Field(None, max_length=256, description="Additional remark")
