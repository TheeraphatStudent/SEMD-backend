from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Union
import secrets

from models.auth_model import (
    AuthLoginRequest, AuthLoginProviderRequest, TwoFAVerifyRequest,
    RefreshTokenRequest, TwoFAEnableRequest, TokenPairResponse,
    PreAuthResponse, TwoFASetupResponse, OAuthDeviceCodeRequest,
    OAuthDeviceCodeResponse, OAuthDevicePollRequest, OAuthAuthorizationRequest,
    OAuthAuthorizationResponse, OAuthCallbackRequest, RegisterRequest,
    RegisterResponse, CreateUserRequest, CreateUserResponse
)
from services.auth_service import AuthService
from services.oauth_service import OAuthService
from services.two_factor_service import TwoFactorService
from database import User
from libs.types.enums import RoleType


class AuthControl:

    def __init__(self):
        pass

    @classmethod
    def login(cls, request: AuthLoginRequest, db: Session) -> Union[TokenPairResponse, PreAuthResponse]:
        user = AuthService.authenticate_user(
            request.username, request.password, db)

        if user.is_2fa_enabled:
            pre_auth_token = AuthService.create_pre_auth_token(user.user_id)
            return PreAuthResponse(
                pre_auth_token=pre_auth_token,
                requires_2fa=True
            )

        access_token = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user, db)

        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer'
        )

    @classmethod
    def login_2fa(cls, request: TwoFAVerifyRequest, db: Session) -> TokenPairResponse:
        payload = AuthService.verify_token(request.pre_auth_token, 'pre_auth')

        user_id = int(payload.get('sub'))
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found'
            )

        if not user.is_2fa_enabled or not user.totp_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='2FA is not enabled for this user'
            )

        if not TwoFactorService.verify_totp(user.totp_secret, request.otp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid OTP code'
            )

        access_token = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user, db)

        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer'
        )

    @classmethod
    async def login_provider(cls, request: AuthLoginProviderRequest, db: Session) -> Union[TokenPairResponse, PreAuthResponse]:
        if request.provider.value == 'github':
            user_info = await OAuthService.exchange_github_token(request.token)
        elif request.provider.value == 'google':
            user_info = await OAuthService.exchange_google_token(request.token)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {request.provider.value}"
            )

        user = OAuthService.upsert_oauth_user(
            provider=request.provider.value,
            oauth_id=user_info['id'],
            email=user_info['email'],
            name=user_info['name'],
            db=db
        )

        if user.is_2fa_enabled:
            pre_auth_token = AuthService.create_pre_auth_token(user.user_id)
            return PreAuthResponse(
                pre_auth_token=pre_auth_token,
                requires_2fa=True
            )

        access_token = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user, db)

        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer'
        )

    @classmethod
    def refresh(cls, request: RefreshTokenRequest, db: Session) -> TokenPairResponse:
        return AuthService.rotate_token_pair(request.refresh_token, db)

    @classmethod
    def logout(cls, refresh_token: str, db: Session):
        AuthService.revoke_refresh_token(refresh_token, db)

    @classmethod
    def setup_2fa(cls, current_user: User, db: Session) -> TwoFASetupResponse:
        secret = TwoFactorService.generate_totp_secret()
        qr_uri = TwoFactorService.get_totp_uri(secret, current_user.email)

        return TwoFASetupResponse(
            secret=secret,
            qr_uri=qr_uri
        )

    @classmethod
    def enable_2fa(cls, request: TwoFAEnableRequest, current_user: User, db: Session):
        if not TwoFactorService.verify_totp(request.secret, request.otp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid OTP code'
            )

        TwoFactorService.enable_2fa(current_user, request.secret, db)

    @classmethod
    async def initiate_device_flow(cls, request: OAuthDeviceCodeRequest) -> OAuthDeviceCodeResponse:
        if request.provider.value == 'github':
            data = await OAuthService.initiate_github_device_flow()
            return OAuthDeviceCodeResponse(
                device_code=data['device_code'],
                user_code=data['user_code'],
                verification_uri=data['verification_uri'],
                expires_in=data['expires_in'],
                interval=data['interval']
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device flow not supported for provider: {request.provider.value}"
            )

    @classmethod
    async def poll_device_flow(cls, request: OAuthDevicePollRequest, db: Session) -> Union[TokenPairResponse, None]:
        if request.provider.value == 'github':
            access_token = await OAuthService.poll_github_device_flow(request.device_code)

            if access_token is None:
                return None

            user_info = await OAuthService.get_github_user_info(access_token)
            user = OAuthService.upsert_oauth_user(
                provider='github',
                oauth_id=user_info['id'],
                email=user_info['email'],
                name=user_info['name'],
                db=db
            )

            if user.is_2fa_enabled:
                pre_auth_token = AuthService.create_pre_auth_token(
                    user.user_id)
                return PreAuthResponse(
                    pre_auth_token=pre_auth_token,
                    requires_2fa=True
                )

            access_token_jwt = AuthService.create_access_token(user)
            refresh_token = AuthService.create_refresh_token(user, db)

            return TokenPairResponse(
                access_token=access_token_jwt,
                refresh_token=refresh_token,
                token_type='bearer'
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device flow not supported for provider: {request.provider.value}"
            )

    @classmethod
    def initiate_oauth_authorization(cls, request: OAuthAuthorizationRequest) -> OAuthAuthorizationResponse:
        state = secrets.token_urlsafe(32)

        if request.provider.value == 'github':
            authorization_url = OAuthService.generate_github_authorization_url(
                state)
        elif request.provider.value == 'google':
            authorization_url = OAuthService.generate_google_authorization_url(
                state)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {request.provider.value}"
            )

        return OAuthAuthorizationResponse(
            authorization_url=authorization_url,
            state=state
        )

    @classmethod
    def register(cls, request: RegisterRequest, db: Session) -> RegisterResponse:
        user = AuthService.register_user(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            password=request.password,
            db=db
        )

        return RegisterResponse(
            status=201,
            message='User registered successfully',
            user_id=user.user_id
        )

    @classmethod
    def create_user(cls, request: CreateUserRequest, current_user: User, db: Session) -> CreateUserResponse:
        if current_user.role != RoleType.SUPER_ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Only SUPER_ADMIN can create admin users'
            )

        user = AuthService.create_user(
            username=request.username,
            email=request.email,
            full_name=request.full_name,
            password=request.password,
            role=request.role,
            db=db
        )

        return CreateUserResponse(
            status=201,
            message='User created successfully',
            user_id=user.user_id
        )

    @classmethod
    async def handle_oauth_callback(cls, provider: str, request: OAuthCallbackRequest, db: Session) -> Union[TokenPairResponse, PreAuthResponse]:
        if provider == 'github':
            access_token = await OAuthService.exchange_github_code(request.code)
            user_info = await OAuthService.get_github_user_info(access_token)

        elif provider == 'google':
            access_token = await OAuthService.exchange_google_code(request.code)
            user_info = await OAuthService.get_google_user_info(access_token)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )

        user = OAuthService.upsert_oauth_user(
            provider=provider,
            user_info=user_info,
            db=db
        )

        if user.is_2fa_enabled:
            pre_auth_token = AuthService.create_pre_auth_token(user.user_id)
            return PreAuthResponse(
                pre_auth_token=pre_auth_token,
                requires_2fa=True
            )

        access_token_jwt = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user, db)

        return TokenPairResponse(
            access_token=access_token_jwt,
            refresh_token=refresh_token,
            token_type='bearer'
        )


auth_control = AuthControl()
