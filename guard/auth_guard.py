"""
Authentication guard for API key and Bearer token verification.
"""

from fastapi import HTTPException, status, Header
from typing import Optional, Dict
from jose import jwt, JWTError
from config.settings import settings


class AuthGuard:

    VALID_API_KEY = settings.api_key
    VALID_JWT_SECRET = settings.jwt_secret
    VALID_JWT_ALGORITHM = settings.jwt_algorithm

    @staticmethod
    def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing x-api-key header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if x_api_key != AuthGuard.VALID_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )

        return x_api_key

    @staticmethod
    def verify_bearer_token(authorization: Optional[str] = Header(None)) -> dict:
        """
        Verify Bearer token from Authorization header.

        Args:
            authorization: Authorization header value

        Returns:
            str: The verified bearer token

        Raises:
            HTTPException: If bearer token is missing or invalid
        """
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

        token = parts[1]
        try:
            payload = jwt.decode(
                token,
                AuthGuard.VALID_JWT_SECRET,
                algorithms=[AuthGuard.VALID_JWT_ALGORITHM],
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid bearer token: {e}",
            )

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
        payload = AuthGuard.verify_bearer_token(authorization)

        return {
            "api_key": api_key,
            "payload": payload,
        }
