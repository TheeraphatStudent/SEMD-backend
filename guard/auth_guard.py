"""
Authentication guard for API key and Bearer token verification.
"""

from fastapi import HTTPException, status, Header, Depends
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from config.settings import settings


def get_db():
    from services.client import postgres_client
    db = postgres_client.get_session_instance()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    from services.client import postgres_client
    db = postgres_client.get_async_session_instance()
    try:
        yield db
    finally:
        await db.close()


class AuthGuard:
    @staticmethod
    def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing x-api-key header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return x_api_key

    @staticmethod
    def verify_bearer_token(authorization: Optional[str] = Header(None)) -> str:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format. Use: Bearer <token>",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return parts[1]

    @staticmethod
    def get_current_user(
        authorization: str = Depends(verify_bearer_token),
        db: Session = Depends(get_db)
    ):
        from services.auth_service import AuthService
        from database import User
        
        payload = AuthService.verify_token(authorization, "access")
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user

    @staticmethod
    def verify_both(
        x_api_key: Optional[str] = Header(None),
        authorization: Optional[str] = Header(None),
    ) -> dict:
        """
        Verify both API key and Bearer token.

        Args:
            x_api_key: API key from header
            authorization: Authorization header value

        Returns:
            dict: Dictionary with verified credentials

        Raises:
            HTTPException: If either credential is invalid
        """
        api_key = AuthGuard.verify_api_key(x_api_key)
        token = AuthGuard.verify_bearer_token(authorization)

        return {
            "api_key": api_key,
            "token": token,
        }
