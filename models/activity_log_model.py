from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ActivityLogModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    activity_log_id: Optional[int] = None
    user_id: Optional[int] = None
    method: str = Field(..., max_length=16)
    endpoint: str = Field(..., max_length=1024)
    request_id: str = Field(..., max_length=32)
    client_ip: Optional[str] = Field(None, max_length=32)
    client_agent: Optional[str] = Field(None, max_length=256)
    response: Optional[str] = Field(None, max_length=512)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
