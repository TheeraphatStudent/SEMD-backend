from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4


class RefreshTokenModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    refresh_tokens_id: Optional[int] = None
    user_id: int
    token_hash: str = Field(..., max_length=64)
    jti: UUID = Field(default_factory=uuid4)
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
