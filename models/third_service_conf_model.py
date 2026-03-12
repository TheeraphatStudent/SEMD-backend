from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ThirdServiceConfModelDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    third_service_conf_id: Optional[int] = None
    service_conf_id: Optional[int] = None
    service_name: str = Field(..., max_length=64)
    base_url: str
    http_method: str = Field(default="GET", max_length=8)
    secret_hash: str
    headers_json: dict = {}
    config_json: dict = {}
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
