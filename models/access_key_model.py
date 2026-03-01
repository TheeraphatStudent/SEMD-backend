from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class AccessKeyModelDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    access_key_id: Optional[int] = None
    user_id: Optional[int] = None
    access_key_hash: str
    expired_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
