from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class AccessKeyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_key_id: Optional[int] = None
    user_id: Optional[int] = None
    key_name: Optional[str] = None
    access_key_hash: str
    is_active: bool = True
    usage_limit: Optional[int] = None
    expired_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
