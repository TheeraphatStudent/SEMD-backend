from pydantic import BaseModel, Field
from typing import Optional
from libs.types.enums import FlagType, ACLType


class UrlFlagCreateRequest(BaseModel):
    url: str = Field(..., description="URL to flag")
    type: FlagType = Field(FlagType.BENIGN, description="Flag type (MALICIOUS or BENIGN)")
    access_level: ACLType = Field(ACLType.PRIVATE, description="Access level (GLOBAL or PRIVATE)")


class UrlFlagUpdateRequest(BaseModel):
    url: Optional[str] = Field(None, description="URL to flag")
    type: Optional[FlagType] = Field(None, description="Flag type (MALICIOUS or BENIGN)")
    access_level: Optional[ACLType] = Field(None, description="Access level (GLOBAL or PRIVATE)")
