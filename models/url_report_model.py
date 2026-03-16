from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from libs.types.enums import FlagType, ReportStatusType


class UrlReportModelDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url_report_id: Optional[int] = None
    user_id: Optional[int] = None
    url: str
    categories: FlagType = FlagType.BENIGN
    status: ReportStatusType = ReportStatusType.PENDING
    remark: Optional[str] = Field(None, max_length=256)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
