from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from libs.types.enums import FlagType, ACLType


class UrlFlagModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url_flag_id: Optional[int] = None
    user_id: Optional[int] = None
    url: str
    type: FlagType = FlagType.BENIGN
    access_level: ACLType = ACLType.PRIVATE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
