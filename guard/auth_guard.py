"""Authentication guard for API key and Bearer token verification."""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session


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


def _verify_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing Authorization header',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Authorization header format. Use: Bearer <token>',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return parts[1]


def _get_current_user(
    authorization: str = Depends(_verify_bearer_token),
    db: Session = Depends(get_db)
):
    from models.db import User
    from services.auth_service import AuthService

    payload = AuthService.verify_token(authorization, 'access')
    user_id = int(payload.get('sub'))
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found'
        )

    return user


def _get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Best-effort caller identity for endpoints that must not require login
    (e.g. the browser extension). Never raises *on an authentication failure*:
    a missing header, a malformed header, an expired/invalid token, or an
    unknown user id all resolve to `None` (anonymous) instead of a 401 -- the
    caller proceeds unauthenticated rather than being hard-blocked. An
    infrastructure failure (e.g. the database session raising) still
    propagates, which is intended -- a broken DB must surface as a 500, not be
    silently downgraded to an anonymous request. `PredictionControl`,
    `UrlFlagService.check_url_flag(_async)`, and `QueueService.add_to_retrain_queue`
    already accept `user`/`user_id=None` end to end, so callers of this
    dependency don't need extra None-handling beyond what they'd do anyway.
    """
    from models.db import User
    from services.auth_service import AuthService

    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    try:
        payload = AuthService.verify_token(parts[1], 'access')
        user_id = int(payload.get('sub'))
    except (HTTPException, ValueError, TypeError):
        return None

    return db.query(User).filter(User.user_id == user_id).first()


def _require_admin(current_user=Depends(_get_current_user)):
    from libs.types.enums import RoleType

    if current_user.role not in (RoleType.ADMIN.value, RoleType.SUPER_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Admin access required',
        )
    return current_user


class AuthGuard:
    # These class attributes are assigned the *same* module-level function
    # objects that internal Depends(...) defaults above reference (rather
    # than being defined as @staticmethod methods that re-wrap a bare name
    # from the class body). That equality matters: FastAPI's
    # `app.dependency_overrides` dict and its per-request dependency cache
    # both key on the exact callable object. Before this fix, `require_admin`
    # depended on a bare `get_current_user` name inside the class body, which
    # bound to the raw `staticmethod` descriptor -- a different object from
    # `AuthGuard.get_current_user` (attribute access unwraps the descriptor)
    # -- so overriding `AuthGuard.get_current_user` in a test silently didn't
    # affect `require_admin` at all. Verified empirically while wiring up
    # Domain 10's ML training router, the first caller of `require_admin`.
    verify_bearer_token = staticmethod(_verify_bearer_token)
    get_current_user = staticmethod(_get_current_user)
    get_current_user_optional = staticmethod(_get_current_user_optional)
    require_admin = staticmethod(_require_admin)

    @staticmethod
    def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Missing x-api-key header',
                headers={'WWW-Authenticate': 'Bearer'},
            )

        return x_api_key

    @staticmethod
    def verify_both(
        x_api_key: Optional[str] = Header(None),
        authorization: Optional[str] = Header(None),
    ) -> dict:
        """Verify both API key and Bearer token.

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
            'api_key': api_key,
            'token': token,
        }
