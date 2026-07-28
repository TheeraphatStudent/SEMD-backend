from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from libs.types.enums import RoleType


class UserModel(BaseModel):
    """Public-facing user profile shape.

    Deliberately excludes password_hash, gg_acc_token/gg_re_token,
    gh_acc_token/gh_re_token, twofa_secret, and ex_acc_token -- these are
    ORM columns on `database.User`, not API-response fields. They were
    previously included here and returned verbatim by GET /auth/me,
    GET /auth/users, and GET /auth/users/{id} (self profile view, and any
    ADMIN viewing any other user), i.e. every OAuth refresh token, the TOTP
    seed, the password hash, and the live extension token were exposed over
    the API. See docs/backend/features/extension-access-codes/README.md.
    `gg_id`/`gh_id` (provider account identifiers, not credentials) and
    `ex_acc_token_exp` (an expiry timestamp, not a secret) are kept since
    they're legitimately useful for a "connected accounts" UI.
    """

    model_config = ConfigDict(from_attributes=True)

    user_id: Optional[int] = None
    username: str = Field(..., max_length=32)
    email: str = Field(..., max_length=64)
    full_name: str = Field(..., max_length=512)
    birthday: Optional[datetime] = None
    role: RoleType = RoleType.MEMBER

    gg_id: Optional[str] = None
    gh_id: Optional[str] = None
    is_2fa_enabled: bool = Field(default=False)

    ex_acc_token_exp: Optional[datetime] = None
    profile_img_uri: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
