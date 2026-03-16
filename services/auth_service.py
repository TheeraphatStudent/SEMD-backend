from datetime import datetime, timedelta
from typing import Optional
import hashlib
import uuid

from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from config.settings import settings
from database import User, RefreshToken
from models.auth_model import TokenPairResponse
from libs.types.enums import RoleType

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class AuthService:

    def __init__(self):
        pass

    @classmethod
    def hash_password(cls, plain: str) -> str:
        return pwd_context.hash(plain)

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @classmethod
    def authenticate_user(cls, username: str, password: str, db: Session) -> User:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid username or password'
            )

        if not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid username or password'
            )

        if not cls.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid username or password'
            )

        return user

    @classmethod
    def create_access_token(cls, user: User) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.auth_access_token_expire_minutes)
        payload = {
            'sub': str(user.user_id),
            'email': user.email,
            'role': user.role,
            'type': 'access',
            'exp': expire
        }
        token = jwt.encode(payload, settings.auth_secret_key,
                           algorithm=settings.auth_algorithm)
        return token

    @classmethod
    def create_refresh_token(cls, user: User, db: Session) -> str:
        jti = uuid.uuid4()
        expire = datetime.utcnow() + timedelta(days=settings.auth_refresh_token_expire_days)

        payload = {
            'sub': str(user.user_id),
            'jti': str(jti),
            'type': 'refresh',
            'exp': expire
        }

        token = jwt.encode(payload, settings.auth_secret_key,
                           algorithm=settings.auth_algorithm)

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        db_refresh_token = RefreshToken(
            user_id=user.user_id,
            token_hash=token_hash,
            jti=jti,
            expires_at=expire,
            is_revoked=False
        )
        db.add(db_refresh_token)
        db.commit()

        return token

    @classmethod
    def create_pre_auth_token(cls, user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(minutes=5)
        payload = {
            'sub': str(user_id),
            'type': 'pre_auth',
            'exp': expire
        }
        token = jwt.encode(payload, settings.auth_secret_key,
                           algorithm=settings.auth_algorithm)
        return token

    @classmethod
    def verify_token(cls, token: str, expected_type: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.auth_secret_key,
                algorithms=[settings.auth_algorithm]
            )

            if payload.get('type') != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {expected_type}"
                )

            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid or expired token: {str(e)}"
            )

    @classmethod
    def rotate_token_pair(cls, refresh_token: str, db: Session) -> TokenPairResponse:
        payload = cls.verify_token(refresh_token, 'refresh')

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid refresh token'
            )

        if db_token.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token has been revoked'
            )

        if db_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Refresh token has expired'
            )

        db_token.is_revoked = True
        db.commit()

        user = db.query(User).filter(User.user_id == db_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User not found'
            )

        new_access_token = cls.create_access_token(user)
        new_refresh_token = cls.create_refresh_token(user, db)

        return TokenPairResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type='bearer'
        )

    @classmethod
    def revoke_refresh_token(cls, refresh_token: str, db: Session):
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()

        if db_token:
            db_token.is_revoked = True
            db.commit()

    @classmethod
    def register_user(cls, username: str, email: str, full_name: str, password: str, db: Session) -> User:
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            if existing_user.username == username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Username already exists'
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Email already exists'
                )

        hashed_password = cls.hash_password(password)

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=hashed_password,
            role=RoleType.MEMBER.value
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    @classmethod
    def create_user(cls, username: str, email: str, full_name: str, password: str, role: RoleType, db: Session) -> User:
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            if existing_user.username == username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Username already exists'
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='Email already exists'
                )

        if role not in [RoleType.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Only ADMIN role can be created through this endpoint'
            )

        hashed_password = cls.hash_password(password)

        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=hashed_password,
            role=role.value
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user


auth_service = AuthService()
