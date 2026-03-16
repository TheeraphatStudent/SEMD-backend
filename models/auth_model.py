from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from models.base_response_model import BaseResponseModel
from libs.types.enums import RoleType, OAuthProviderType


class AuthLoginRequest(BaseModel):
    username: str = Field(
        title='username',
        description='Username for login'
    )

    password: str = Field(
        title='password',
        description='Password for login'
    )


class AuthLoginProviderRequest(BaseModel):
    provider: OAuthProviderType = Field(
        title='provider',
        description='Authentication provider (e.g., google, github)'
    )

    token: str = Field(
        title='token',
        description='Authentication token from provider',
    )


class AuthTwoFactorRequest(BaseModel):
    code: str = Field(
        title='code',
        description='Two-factor authentication code',
    )


# ------------- Response

class AuthLoginResponse(BaseResponseModel):
    message: str = Field(
        title='message',
        description='Response message',
        examples=['Login successful'],
    )
    data: AuthLoginRequest = Field(
        title='data',
        description='Login data',
    )


class TokenPairResponse(BaseResponseModel):
    status: int = 200
    message: str = 'Authentication successful'
    access_token: str = Field(
        title='access_token',
        description='JWT access token',
    )
    refresh_token: str = Field(
        title='refresh_token',
        description='JWT refresh token',
    )
    token_type: str = Field(
        default='bearer',
        title='token_type',
        description='Token type',
    )


class PreAuthResponse(BaseResponseModel):
    status: int = 200
    message: str = '2FA verification required'
    pre_auth_token: str = Field(
        title='pre_auth_token',
        description='Pre-authentication token for 2FA',
    )
    requires_2fa: bool = Field(
        default=True,
        title='requires_2fa',
        description='Indicates 2FA is required',
    )


class TwoFAVerifyRequest(BaseModel):
    pre_auth_token: str = Field(
        title='pre_auth_token',
        description='Pre-authentication token',
    )
    otp_code: str = Field(
        title='otp_code',
        description='One-time password code',
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        title='refresh_token',
        description='Refresh token to exchange for new token pair',
    )


class TwoFASetupResponse(BaseResponseModel):
    status: int = 200
    message: str = '2FA setup initiated'
    secret: str = Field(
        title='secret',
        description='TOTP secret key',
    )
    qr_uri: str = Field(
        title='qr_uri',
        description='QR code URI for authenticator apps',
    )


class TwoFAEnableRequest(BaseModel):
    secret: str = Field(
        title='secret',
        description='TOTP secret key to enable',
    )
    otp_code: str = Field(
        title='otp_code',
        description='One-time password code to verify',
    )


class OAuthDeviceCodeRequest(BaseModel):
    provider: OAuthProviderType = Field(
        title='provider',
        description='OAuth provider (github or google)'
    )


class OAuthDeviceCodeResponse(BaseResponseModel):
    status: int = 200
    message: str = 'Device code generated'
    device_code: str = Field(
        title='device_code',
        description='Device verification code',
    )
    user_code: str = Field(
        title='user_code',
        description='User verification code to enter',
    )
    verification_uri: str = Field(
        title='verification_uri',
        description='URL where user enters the code',
    )
    expires_in: int = Field(
        title='expires_in',
        description='Seconds until code expires',
    )
    interval: int = Field(
        title='interval',
        description='Minimum seconds between polling requests',
    )


class OAuthDevicePollRequest(BaseModel):
    provider: OAuthProviderType = Field(
        title='provider',
        description='OAuth provider'
    )
    device_code: str = Field(
        title='device_code',
        description='Device code to poll',
    )


class OAuthAuthorizationRequest(BaseModel):
    provider: OAuthProviderType = Field(
        title='provider',
        description='OAuth provider (github or google)'
    )


class OAuthAuthorizationResponse(BaseResponseModel):
    status: int = 200
    message: str = 'Authorization URL generated'
    authorization_url: str = Field(
        title='authorization_url',
        description='URL to redirect user for authorization',
    )
    state: str = Field(
        title='state',
        description='State parameter for CSRF protection',
    )


class OAuthCallbackRequest(BaseModel):
    code: str = Field(
        title='code',
        description='Authorization code from OAuth provider',
    )
    state: str = Field(
        title='state',
        description='State parameter for verification',
    )


class RegisterRequest(BaseModel):
    username: str = Field(
        title='username',
        description='Username for registration',
        min_length=3,
        max_length=32
    )
    email: EmailStr = Field(
        title='email',
        description='Email address'
    )
    full_name: str = Field(
        title='full_name',
        description='Full name of the user',
        max_length=512
    )
    password: str = Field(
        title='password',
        description='Password for the account',
        min_length=8
    )


class RegisterResponse(BaseResponseModel):
    status: int = 201
    message: str = 'User registered successfully'
    user_id: int = Field(
        title='user_id',
        description='ID of the newly created user'
    )


class CreateUserRequest(BaseModel):
    username: str = Field(
        title='username',
        description='Username for the new user',
        min_length=3,
        max_length=32
    )
    email: EmailStr = Field(
        title='email',
        description='Email address'
    )
    full_name: str = Field(
        title='full_name',
        description='Full name of the user',
        max_length=512
    )
    password: str = Field(
        title='password',
        description='Password for the account',
        min_length=8
    )
    role: RoleType = Field(
        title='role',
        description='Role for the new user (ADMIN only)',
        default=RoleType.ADMIN
    )


class CreateUserResponse(BaseResponseModel):
    status: int = 201
    message: str = 'User created successfully'
    user_id: int = Field(
        title='user_id',
        description='ID of the newly created user'
    )
