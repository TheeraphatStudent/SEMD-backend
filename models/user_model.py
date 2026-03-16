from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from libs.types.enums import RoleType


class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: Optional[int] = None
    username: str = Field(..., max_length=32)
    email: str = Field(..., max_length=64)
    full_name: str = Field(..., max_length=512)
    birthday: Optional[datetime] = None
    password_hash: str = Field(..., max_length=1024)
    role: RoleType = RoleType.MEMBER

    gg_id: Optional[str] = None
    gg_acc_token: Optional[str] = None
    gg_re_token: Optional[str] = None
    gh_id: Optional[str] = None
    gh_acc_token: Optional[str] = None
    gh_re_token: Optional[str] = None
    twofa_secret: Optional[str] = None
    is_2fa_enabled: bool = Field(default=False)

    ex_acc_token: Optional[str] = None
    ex_acc_token_exp: Optional[datetime] = None
    profile_img_uri: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
