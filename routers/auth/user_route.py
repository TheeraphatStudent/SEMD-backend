from typing import List

from fastapi import Depends, HTTPException
from pydantic import Field
from sqlalchemy.orm import Session

from control.auth_control import AuthControl
from models.db import User
from guard.auth_guard import AuthGuard, get_db
from libs.pagination import PaginationMeta, PaginationParams, create_pagination_meta
from libs.types.enums import RoleType
from models import BaseResponseModel
from models.auth.user_model import UserModel
from models.auth.user_request import AdminCreateUserRequest, AdminPasswordResetRequest, AdminUpdateUserRequest
from routers import BaseRoute


class UserListResponse(BaseResponseModel):
    data: List[UserModel] = Field(title="data", description="List of users")
    pagination: PaginationMeta = Field(title="pagination", description="Pagination metadata")


class UserResponse(BaseResponseModel):
    data: UserModel = Field(title="data", description="User data")


class UserRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/auth/users",
            tags=["admin-users"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}, 422: {"description": "Validation error"}}
        )

        self.router.get(
            "",
            response_model=UserListResponse,
            summary="[Admin] Get All Users",
            description="Get all users with pagination. Admin only."
        )(self.get_all_users)
        
        self.router.post(
            "",
            response_model=UserResponse,
            summary="[Admin] Create User",
            description="Create a new user with password. Admin can create MEMBER users, Master Admin can create ADMIN users."
        )(self.create_user)
        
        self.router.get(
            "/{user_id}",
            response_model=UserResponse,
            summary="[Admin] Get User by ID",
            description="Get user details by ID. Admin only."
        )(self.get_user_by_id)
        
        self.router.put(
            "/{user_id}",
            response_model=UserResponse,
            summary="[Admin] Update User",
            description="Update user details. Master Admin can change roles, Admin cannot."
        )(self.update_user)
        
        self.router.post(
            "/{user_id}/reset-password",
            response_model=BaseResponseModel,
            summary="[Admin] Reset User Password",
            description="Reset user's password. Admin can reset MEMBER passwords, Master Admin can reset any password."
        )(self.reset_user_password)
        
        self.router.delete(
            "/{user_id}",
            response_model=BaseResponseModel,
            summary="[Admin] Delete User",
            description="Delete user. Admin can delete MEMBER users, Master Admin can delete any user except other Master Admins."
        )(self.delete_user)

    def _check_admin_permission(self, user: User):
        """Check if user has admin or master admin role"""
        if user.role not in [RoleType.ADMIN.value, RoleType.SUPER_ADMIN.value]:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )

    async def get_all_users(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db),
        pagination: PaginationParams = Depends()
    ):
        self._check_admin_permission(current_user)
        users, total = AuthControl.admin_get_all_users(db, pagination.offset, pagination.limit)
        meta = create_pagination_meta(pagination.page, pagination.page_size, total)
        return UserListResponse(
            status=200,
            message="Users retrieved successfully",
            data=users,
            pagination=meta
        )

    async def create_user(
        self,
        request: AdminCreateUserRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin_permission(current_user)
        new_user = AuthControl.admin_create_user(request, current_user, db)
        return UserResponse(
            status=201,
            message="User created successfully",
            data=new_user
        )

    async def get_user_by_id(
        self,
        user_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin_permission(current_user)
        user = AuthControl.admin_get_user_by_id(user_id, db)
        return UserResponse(
            status=200,
            message="User retrieved successfully",
            data=user
        )

    async def update_user(
        self,
        user_id: int,
        request: AdminUpdateUserRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin_permission(current_user)
        updated_user = AuthControl.admin_update_user(user_id, request, current_user, db)
        return UserResponse(
            status=200,
            message="User updated successfully",
            data=updated_user
        )

    async def reset_user_password(
        self,
        user_id: int,
        request: AdminPasswordResetRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin_permission(current_user)
        AuthControl.admin_reset_user_password(user_id, request, current_user, db)
        return BaseResponseModel(
            status=200,
            message="User password reset successfully"
        )

    async def delete_user(
        self,
        user_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin_permission(current_user)
        AuthControl.admin_delete_user(user_id, current_user, db)
        return BaseResponseModel(
            status=200,
            message="User deleted successfully"
        )