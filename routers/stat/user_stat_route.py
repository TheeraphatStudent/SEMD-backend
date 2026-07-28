from fastapi import Depends

from core.exceptions import NotImplementedFeatureError
from models.db import User
from guard.auth_guard import AuthGuard
from models import TopUserResponse, UserActivityResponse, UserRoleStatResponse, UserStatResponse
from routers import BaseRoute


class UserStatRoute(BaseRoute):
    """See routers/dashboard/dashboard_route.py's docstring -- same finding
    (unauthenticated `pass` stubs failing response validation on every call),
    same fix (authenticated, honest 501 via NotImplementedFeatureError).
    Whether these should be admin-only vs any-authenticated-user is itself
    an undefined-metric-semantics question (same category as the master
    prompt's "do not invent requirements") -- left as any-authenticated for
    now; revisit when the actual aggregation logic is built."""

    def __init__(self):
        super().__init__(
            prefix="/stat/user",
            tags=["stat-user"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get('', response_model=UserStatResponse)(self.get_user_stat)
        self.router.get('/activity', response_model=UserActivityResponse)(self.get_user_activity)
        self.router.get('/role', response_model=UserRoleStatResponse)(self.get_user_role)
        self.router.get('/top', response_model=TopUserResponse)(self.get_top_users)

    async def get_user_stat(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('User statistics are not implemented yet')

    async def get_user_activity(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('User activity statistics are not implemented yet')

    async def get_user_role(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('User role statistics are not implemented yet')

    async def get_top_users(self, current_user: User = Depends(AuthGuard.get_current_user)):
        raise NotImplementedFeatureError('Top-user statistics are not implemented yet')
