from routers import BaseRoute
from models import BaseResponseModel
from models.access_key_request import (
    AccessKeyCreateRequest,
    AccessKeyAdminCreateRequest, AccessKeyAdminUpdateRequest
)
from fastapi import HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Any, List
from pydantic import Field

from control.access_key_control import AccessKeyControl
from guard.auth_guard import AuthGuard, get_db
from database import User
from libs.pagination import PaginationParams, PaginationMeta
from libs.types.enums import RoleType


class AccessKeyResponse(BaseResponseModel):
    data: Any = Field(title="data", description="Access Key data")


class AccessKeyListResponse(BaseResponseModel):
    data: List[Any] = Field(title="data", description="List of Access Keys")
    pagination: PaginationMeta = Field(title="pagination", description="Pagination metadata")


class AccessKeyRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/setting/access-key",
            tags=["access-key"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 422: {"description": "Validation error"}}
        )

        self.router.get(
            "/me",
            response_model=AccessKeyListResponse,
            summary="Get My Access Keys",
            description="Get all access keys for the current user with pagination."
        )(self.get_my_keys)
        
        self.router.post(
            "",
            response_model=AccessKeyResponse,
            summary="Create Access Key",
            description="Create a new access key. Returns the raw key only once."
        )(self.create_key)
        
        self.router.post(
            "/{key_id}/reset",
            response_model=AccessKeyResponse,
            summary="Reset Access Key",
            description="Reset an access key. Old key becomes inactive, new key is generated."
        )(self.reset_key)
        
        self.router.get(
            "/{key_id}/usage/monthly",
            response_model=AccessKeyResponse,
            summary="Get Monthly Usage",
            description="Get usage statistics for a specific month."
        )(self.get_usage_monthly)
        
        self.router.get(
            "/{key_id}/usage/yearly",
            response_model=AccessKeyResponse,
            summary="Get Yearly Usage",
            description="Get usage statistics for a specific year."
        )(self.get_usage_yearly)
        
        self.router.get(
            "/{key_id}/usage",
            response_model=AccessKeyResponse,
            summary="Get All Time Usage",
            description="Get all-time usage statistics."
        )(self.get_usage_all_time)
        
        self.router.get(
            "/admin",
            response_model=AccessKeyListResponse,
            summary="[Admin] Get All Access Keys",
            description="Get all access keys in the system. Admin only."
        )(self.admin_get_all_keys)
        
        self.router.post(
            "/admin",
            response_model=AccessKeyResponse,
            summary="[Admin] Create Access Key for User",
            description="Create an access key for a specific user with usage limit. Admin only."
        )(self.admin_create_key)
        
        self.router.put(
            "/admin/{key_id}",
            response_model=AccessKeyResponse,
            summary="[Admin] Update Access Key",
            description="Update an access key (set limit, activate/deactivate). Admin only."
        )(self.admin_update_key)
        
        self.router.delete(
            "/admin/{key_id}",
            response_model=BaseResponseModel,
            summary="[Admin] Delete Access Key",
            description="Delete an access key. Admin only."
        )(self.admin_delete_key)
        
        self.router.get(
            "/admin/{key_id}/usage/monthly",
            response_model=AccessKeyResponse,
            summary="[Admin] Get Monthly Usage",
            description="Get usage statistics for any key. Admin only."
        )(self.admin_get_usage_monthly)
        
        self.router.get(
            "/admin/{key_id}/usage/yearly",
            response_model=AccessKeyResponse,
            summary="[Admin] Get Yearly Usage",
            description="Get yearly usage statistics for any key. Admin only."
        )(self.admin_get_usage_yearly)
        
        self.router.get(
            "/admin/{key_id}/usage",
            response_model=AccessKeyResponse,
            summary="[Admin] Get All Time Usage",
            description="Get all-time usage statistics for any key. Admin only."
        )(self.admin_get_usage_all_time)

    def _check_admin(self, user: User):
        if user.role not in [RoleType.ADMIN.value, RoleType.SUPER_ADMIN.value]:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )

    async def create_key(
        self,
        request: AccessKeyCreateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            result = AccessKeyControl.create_key(current_user, request, db)
            return AccessKeyResponse(
                status=201,
                message="Access key created successfully. Save the access_key, it won't be shown again.",
                data=result
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def reset_key(
        self,
        key_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            result = AccessKeyControl.reset_key(current_user, key_id, db)
            return AccessKeyResponse(
                status=200,
                message="Access key reset successfully. Save the new access_key, it won't be shown again.",
                data=result
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_my_keys(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db),
        pagination: PaginationParams = Depends()
    ):
        try:
            keys, meta = AccessKeyControl.get_user_keys(current_user, pagination, db)
            return AccessKeyListResponse(
                status=200,
                message="Access keys retrieved successfully",
                data=keys,
                pagination=meta
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_usage_monthly(
        self,
        key_id: int,
        year: int = Query(..., ge=2020, description="Year"),
        month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            result = AccessKeyControl.get_key_usage_monthly(current_user, key_id, year, month, db)
            return AccessKeyResponse(status=200, message="Monthly usage retrieved", data=result)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_usage_yearly(
        self,
        key_id: int,
        year: int = Query(..., ge=2020, description="Year"),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            result = AccessKeyControl.get_key_usage_yearly(current_user, key_id, year, db)
            return AccessKeyResponse(status=200, message="Yearly usage retrieved", data=result)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_usage_all_time(
        self,
        key_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            result = AccessKeyControl.get_key_usage_all_time(current_user, key_id, db)
            return AccessKeyResponse(status=200, message="All-time usage retrieved", data=result)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def admin_get_all_keys(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db),
        pagination: PaginationParams = Depends()
    ):
        self._check_admin(current_user)
        try:
            keys, meta = AccessKeyControl.admin_get_all_keys(pagination, db)
            return AccessKeyListResponse(
                status=200,
                message="All access keys retrieved",
                data=keys,
                pagination=meta
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def admin_create_key(
        self,
        request: AccessKeyAdminCreateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin(current_user)
        try:
            result = AccessKeyControl.admin_create_key(request, db)
            return AccessKeyResponse(
                status=201,
                message="Access key created for user. Save the access_key, it won't be shown again.",
                data=result
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def admin_update_key(
        self,
        key_id: int,
        request: AccessKeyAdminUpdateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin(current_user)
        try:
            result = AccessKeyControl.admin_update_key(key_id, request, db)
            return AccessKeyResponse(status=200, message="Access key updated", data=result)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def admin_delete_key(
        self,
        key_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin(current_user)
        try:
            AccessKeyControl.admin_delete_key(key_id, db)
            return BaseResponseModel(status=200, message="Access key deleted")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def admin_get_usage_monthly(
        self,
        key_id: int,
        year: int = Query(..., ge=2020, description="Year"),
        month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin(current_user)
        try:
            result = AccessKeyControl.admin_get_key_usage_monthly(key_id, year, month, db)
            return AccessKeyResponse(status=200, message="Monthly usage retrieved", data=result)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def admin_get_usage_yearly(
        self,
        key_id: int,
        year: int = Query(..., ge=2020, description="Year"),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin(current_user)
        try:
            result = AccessKeyControl.admin_get_key_usage_yearly(key_id, year, db)
            return AccessKeyResponse(status=200, message="Yearly usage retrieved", data=result)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def admin_get_usage_all_time(
        self,
        key_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin(current_user)
        try:
            result = AccessKeyControl.admin_get_key_usage_all_time(key_id, db)
            return AccessKeyResponse(status=200, message="All-time usage retrieved", data=result)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
