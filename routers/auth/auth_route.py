from typing import Union

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from control.auth_control import AuthControl
from models.db import User
from guard.auth_guard import AuthGuard, get_db
from libs.types.enums import OAuthProviderType
from models.auth.auth_model import (
    AuthLoginProviderRequest,
    AuthLoginRequest,
    CreateUserRequest,
    CreateUserResponse,
    OAuthAuthorizationRequest,
    OAuthAuthorizationResponse,
    OAuthCallbackRequest,
    OAuthDeviceCodeRequest,
    OAuthDeviceCodeResponse,
    OAuthDevicePollRequest,
    PreAuthResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RegisterResponse,
    TokenPairResponse,
    TwoFAEnableRequest,
    TwoFASetupResponse,
    TwoFAVerifyRequest,
)
from models.common.base_response_model import BaseResponseModel
from models.auth.user_model import UserModel
from models.auth.user_request import PasswordResetRequest, UserUpdateRequest
from routers import BaseRoute


class AuthRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/auth",
            tags=["auth"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 422: {"description": "Validation error"}}
        )

        self.router.post(
            "/register",
            response_model=RegisterResponse,
            summary="User Registration",
            description="Register a new user account with MEMBER role. Public endpoint."
        )(self.register)
        
        self.router.post(
            "/create",
            response_model=CreateUserResponse,
            summary="Create Admin User",
            description="Create a new ADMIN user. Requires SUPER_ADMIN role."
        )(self.create_user)
        
        self.router.post(
            "/login",
            response_model=Union[TokenPairResponse, PreAuthResponse],
            summary="User Login",
            description="Authenticate user with username and password. Returns token pair or pre-auth token if 2FA is enabled."
        )(self.login)
        
        self.router.post(
            "/login/2fa",
            response_model=TokenPairResponse,
            summary="Complete 2FA Login",
            description="Complete authentication with 2FA verification code after receiving pre-auth token."
        )(self.login_2fa)
        
        self.router.post(
            "/login/provider",
            response_model=Union[TokenPairResponse, PreAuthResponse],
            summary="OAuth Provider Login",
            description="Authenticate using OAuth provider (GitHub or Google) token."
        )(self.login_provider)
        
        self.router.post(
            "/refresh",
            response_model=TokenPairResponse,
            summary="Refresh Access Token",
            description="Exchange refresh token for a new token pair."
        )(self.refresh)
        
        self.router.post(
            "/logout",
            response_model=BaseResponseModel,
            summary="User Logout",
            description="Revoke refresh token and logout user."
        )(self.logout)
        
        self.router.post(
            "/2fa/setup",
            response_model=TwoFASetupResponse,
            summary="Setup 2FA",
            description="Generate TOTP secret and QR code for 2FA setup. Requires authentication."
        )(self.setup_2fa)
        
        self.router.post(
            "/2fa/enable",
            response_model=BaseResponseModel,
            summary="Enable 2FA",
            description="Enable 2FA for the authenticated user by verifying OTP code. Requires authentication."
        )(self.enable_2fa)

        # OAuth

        self.router.post(
            "/oauth/device",
            response_model=OAuthDeviceCodeResponse,
            summary="Initiate OAuth Device Flow",
            description="Start OAuth device authorization flow for GitHub. Returns device code and user code."
        )(self.oauth_device_initiate)
        
        self.router.post(
            "/oauth/device/poll",
            response_model=Union[TokenPairResponse, PreAuthResponse, BaseResponseModel],
            summary="Poll OAuth Device Flow",
            description="Poll for OAuth device flow completion. Returns token pair when authorized or pending status."
        )(self.oauth_device_poll)
        
        self.router.post(
            "/oauth/authorize",
            response_model=OAuthAuthorizationResponse,
            summary="Get OAuth Authorization URL",
            description="Generate OAuth authorization URL for GitHub or Google login."
        )(self.oauth_authorize)
        
        self.router.get(
            "/callback/{provider}",
            response_model=Union[TokenPairResponse, PreAuthResponse],
            summary="OAuth Callback",
            description="Handle OAuth callback from provider. Exchanges authorization code for tokens."
        )(self.oauth_callback)
        
        self.router.get(
            "/me",
            response_model=UserModel,
            summary="Get My Profile",
            description="Get current user's profile information. Requires authentication."
        )(self.get_me)
        
        self.router.put(
            "/me",
            response_model=UserModel,
            summary="Update My Profile",
            description="Update current user's profile information. Requires authentication."
        )(self.update_me)
        
        self.router.post(
            "/me/reset-password",
            response_model=BaseResponseModel,
            summary="Reset My Password",
            description="Reset current user's password. Requires current password verification."
        )(self.reset_password)

    async def login(self, request: AuthLoginRequest, db: Session = Depends(get_db)):
        return AuthControl.login(request, db)

    async def login_2fa(self, request: TwoFAVerifyRequest, db: Session = Depends(get_db)):
        return AuthControl.login_2fa(request, db)

    async def login_provider(self, request: AuthLoginProviderRequest, db: Session = Depends(get_db)):
        return await AuthControl.login_provider(request, db)

    async def refresh(self, request: RefreshTokenRequest, db: Session = Depends(get_db)):
        return AuthControl.refresh(request, db)

    async def logout(self, request: RefreshTokenRequest, db: Session = Depends(get_db)):
        AuthControl.logout(request.refresh_token, db)
        return BaseResponseModel(status=200, message="Logged out successfully")

    async def setup_2fa(self, current_user: User = Depends(AuthGuard.get_current_user), db: Session = Depends(get_db)):
        return AuthControl.setup_2fa(current_user, db)

    async def enable_2fa(self, request: TwoFAEnableRequest, current_user: User = Depends(AuthGuard.get_current_user), db: Session = Depends(get_db)):
        AuthControl.enable_2fa(request, current_user, db)
        return BaseResponseModel(status=200, message="2FA enabled successfully")

    async def oauth_device_initiate(self, request: OAuthDeviceCodeRequest):
        return await AuthControl.initiate_device_flow(request)

    async def oauth_device_poll(self, request: OAuthDevicePollRequest, db: Session = Depends(get_db)):
        result = await AuthControl.poll_device_flow(request, db)
        if result is None:
            return BaseResponseModel(status=202, message="Authorization pending")
        return result

    async def oauth_authorize(self, request: OAuthAuthorizationRequest):
        return AuthControl.initiate_oauth_authorization(request)

    async def oauth_callback(self, provider: OAuthProviderType, code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
        request = OAuthCallbackRequest(code=code, state=state)
        return await AuthControl.handle_oauth_callback(provider.value, request, db)

    async def register(self, request: RegisterRequest, db: Session = Depends(get_db)):
        return AuthControl.register(request, db)

    async def create_user(self, request: CreateUserRequest, current_user: User = Depends(AuthGuard.get_current_user), db: Session = Depends(get_db)):
        return AuthControl.create_user(request, current_user, db)

    async def get_me(self, current_user: User = Depends(AuthGuard.get_current_user)):
        return AuthControl.get_user_profile(current_user)

    async def update_me(self, request: UserUpdateRequest, current_user: User = Depends(AuthGuard.get_current_user), db: Session = Depends(get_db)):
        return AuthControl.update_user_profile(current_user, request, db)

    async def reset_password(self, request: PasswordResetRequest, current_user: User = Depends(AuthGuard.get_current_user), db: Session = Depends(get_db)):
        AuthControl.reset_password(current_user, request, db)
        return BaseResponseModel(status=200, message="Password reset successfully")
