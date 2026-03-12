from routers import BaseRoute
from models.auth_model import (
    AuthLoginRequest, AuthLoginProviderRequest, TwoFAVerifyRequest,
    RefreshTokenRequest, TwoFAEnableRequest, TokenPairResponse,
    PreAuthResponse, TwoFASetupResponse, OAuthDeviceCodeRequest,
    OAuthDeviceCodeResponse, OAuthDevicePollRequest, OAuthAuthorizationRequest,
    OAuthAuthorizationResponse, OAuthCallbackRequest, RegisterRequest,
    RegisterResponse, CreateUserRequest, CreateUserResponse
)
from models.base_response_model import BaseResponseModel
from fastapi import HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Union, Optional

from services.client import postgres_client
from control.auth_control import AuthControl
from guard.auth_guard import AuthGuard
from database import User
from libs.types.enums import OAuthProviderType

def get_db():
    db = postgres_client.get_session_instance()
    try:
        yield db
    finally:
        db.close()

def get_current_user(authorization: str = Depends(AuthGuard.verify_bearer_token), db: Session = Depends(get_db)) -> User:
    from services.auth_service import AuthService
    payload = AuthService.verify_token(authorization.split()[1] if " " in authorization else authorization, "access")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

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

    async def login(self, request: AuthLoginRequest, db: Session = Depends(get_db)):
        try:
            return AuthControl.login(request, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def login_2fa(self, request: TwoFAVerifyRequest, db: Session = Depends(get_db)):
        try:
            return AuthControl.login_2fa(request, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def login_provider(self, request: AuthLoginProviderRequest, db: Session = Depends(get_db)):
        try:
            return await AuthControl.login_provider(request, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def refresh(self, request: RefreshTokenRequest, db: Session = Depends(get_db)):
        try:
            return AuthControl.refresh(request, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def logout(self, request: RefreshTokenRequest, db: Session = Depends(get_db)):
        try:
            AuthControl.logout(request.refresh_token, db)
            return BaseResponseModel(status=200, message="Logged out successfully")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def setup_2fa(self, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        try:
            return AuthControl.setup_2fa(current_user, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def enable_2fa(self, request: TwoFAEnableRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        try:
            AuthControl.enable_2fa(request, current_user, db)
            return BaseResponseModel(status=200, message="2FA enabled successfully")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def oauth_device_initiate(self, request: OAuthDeviceCodeRequest):
        try:
            return await AuthControl.initiate_device_flow(request)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def oauth_device_poll(self, request: OAuthDevicePollRequest, db: Session = Depends(get_db)):
        try:
            result = await AuthControl.poll_device_flow(request, db)
            if result is None:
                return BaseResponseModel(status=202, message="Authorization pending")
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def oauth_authorize(self, request: OAuthAuthorizationRequest):
        try:
            return AuthControl.initiate_oauth_authorization(request)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def oauth_callback(self, provider: OAuthProviderType, code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
        try:
            request = OAuthCallbackRequest(code=code, state=state)
            return await AuthControl.handle_oauth_callback(provider.value, request, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def register(self, request: RegisterRequest, db: Session = Depends(get_db)):
        try:
            return AuthControl.register(request, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_user(self, request: CreateUserRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        try:
            return AuthControl.create_user(request, current_user, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
