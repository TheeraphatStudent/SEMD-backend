from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from libs.types.enums import ServiceType

class ServiceConfModelDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    service_conf_id: Optional[int] = None
    user_id: Optional[int] = None
    service_name: str = Field(..., max_length=32)
    service_type: ServiceType
    is_active: bool = True
    version_no: str = Field(..., max_length=12)
    config_uri: str
    config_json: dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
