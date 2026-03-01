from pydantic import BaseModel, Field
from typing import Optional
from models.base_response_model import BaseResponseModel

class AuthLoginRequest(BaseModel):
    username: str = Field(
        title="username",
        description="Username for login"
    )

    password: str = Field(
        title="password",
        description="Password for login"
    )

class AuthLoginProviderRequest(BaseModel):
    provider: str = Field(
        title="provider",
        description="Authentication provider (e.g., google, github)",
        examples=["google", "github"],
    )

    token: str = Field(
        title="token",
        description="Authentication token from provider",
    )

class AuthTwoFactorRequest(BaseModel):
    code: str = Field(
        title="code",
        description="Two-factor authentication code",
    )


# ------------- Response

class AuthLoginResponse(BaseResponseModel):
    message: str = Field(
        title="message",
        description="Response message",
        examples=["Login successful"],
    )
    data: AuthLoginRequest = Field(
        title="data",
        description="Login data",
    )