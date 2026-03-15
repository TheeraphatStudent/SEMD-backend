from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class SystemConfigModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    system_config_id: Optional[int] = None
    config_key: str
    config_value: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SystemConfigUpdateRequest(BaseModel):
    config_value: str = Field(..., description="New value for the config")
    description: Optional[str] = Field(None, description="Optional description update")
