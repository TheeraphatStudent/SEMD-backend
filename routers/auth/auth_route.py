from routers import BaseRoute
from models.auth_model import (
    AuthLoginRequest, AuthLoginProviderRequest, TwoFAVerifyRequest,
    RefreshTokenRequest, TwoFAEnableRequest, TokenPairResponse,
    PreAuthResponse, TwoFASetupResponse, OAuthDeviceCodeRequest,
    OAuthDeviceCodeResponse, OAuthDevicePollRequest, OAuthAuthorizationRequest,
    OAuthAuthorizationResponse, OAuthCallbackRequest
)
from models.base_response_model import BaseResponseModel
from fastapi import HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Union, Optional

from services.postgres_client import postgres_client
from control.auth_control import AuthControl
from guard.auth_guard import AuthGuard
from database.user import User

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
        
        self.router.post("/login", response_model=Union[TokenPairResponse, PreAuthResponse])(self.login)
        self.router.post("/login/2fa", response_model=TokenPairResponse)(self.login_2fa)
        self.router.post("/login/provider", response_model=Union[TokenPairResponse, PreAuthResponse])(self.login_provider)
        self.router.post("/refresh", response_model=TokenPairResponse)(self.refresh)
        self.router.post("/logout", response_model=BaseResponseModel)(self.logout)
        self.router.post("/2fa/setup", response_model=TwoFASetupResponse)(self.setup_2fa)
        self.router.post("/2fa/enable", response_model=BaseResponseModel)(self.enable_2fa)
        
        self.router.post("/oauth/device", response_model=OAuthDeviceCodeResponse)(self.oauth_device_initiate)
        self.router.post("/oauth/device/poll", response_model=Union[TokenPairResponse, PreAuthResponse, BaseResponseModel])(self.oauth_device_poll)
        self.router.post("/oauth/authorize", response_model=OAuthAuthorizationResponse)(self.oauth_authorize)
        self.router.get("/callback/{provider}", response_model=Union[TokenPairResponse, PreAuthResponse])(self.oauth_callback)

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

    async def oauth_callback(self, provider: str, code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
        try:
            callback_request = OAuthCallbackRequest(code=code, state=state)
            return await AuthControl.handle_oauth_callback(provider, callback_request, db)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
