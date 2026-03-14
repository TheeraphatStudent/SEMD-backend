from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from libs.types.enums import UsageLogType

class UsageLogModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    usage_log_id: Optional[int] = None
    service_id: Optional[int] = None
    access_key_id: Optional[int] = None
    prediction_id: Optional[int] = None
    type: UsageLogType
    created_at: datetime = Field(default_factory=datetime.utcnow)
