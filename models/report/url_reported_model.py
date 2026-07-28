from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UrlReportedModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url_reported_id: Optional[int] = None
    url_report_id: int
    user_id: int
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    remark: Optional[str] = Field(None, max_length=256)
    created_at: datetime = Field(default_factory=datetime.utcnow)
