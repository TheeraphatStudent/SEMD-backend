from routers import BaseRoute
from models import BaseResponseModel
from models.url_flag_request import UrlFlagCreateRequest, UrlFlagUpdateRequest
from fastapi import HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Any
from pydantic import Field

from control.url_flag_control import UrlFlagControl
from guard.auth_guard import AuthGuard, get_db
from database import User


class UrlFlagResponse(BaseResponseModel):
    data: Any = Field(title="data", description="URL Flag data")


class UrlFlagListResponse(BaseResponseModel):
    data: List[Any] = Field(title="data", description="List of URL Flags")


class UrlFlagRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/setting/url-flag",
            tags=["url-flag"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 422: {"description": "Validation error"}}
        )

        self.router.get(
            "",
            response_model=UrlFlagListResponse,
            summary="Get All URL Flags",
            description="Get all URL flags. Requires authentication."
        )(self.get_all_flags)
        
        self.router.get(
            "/me",
            response_model=UrlFlagListResponse,
            summary="Get My URL Flags",
            description="Get URL flags created by the current user."
        )(self.get_my_flags)
        
        self.router.get(
            "/{flag_id}",
            response_model=UrlFlagResponse,
            summary="Get URL Flag by ID",
            description="Get a specific URL flag by its ID."
        )(self.get_flag_by_id)
        
        self.router.post(
            "",
            response_model=UrlFlagResponse,
            summary="Create URL Flag",
            description="Create a new URL flag. Requires authentication."
        )(self.create_flag)
        
        self.router.put(
            "/{flag_id}",
            response_model=UrlFlagResponse,
            summary="Update URL Flag",
            description="Update an existing URL flag. Requires authentication."
        )(self.update_flag)
        
        self.router.delete(
            "/{flag_id}",
            response_model=BaseResponseModel,
            summary="Delete URL Flag",
            description="Delete an existing URL flag. Requires authentication."
        )(self.delete_flag)

    async def create_flag(
        self,
        request: UrlFlagCreateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            flag = UrlFlagControl.create_flag(current_user, request, db)
            return UrlFlagResponse(status=201, message="URL Flag created successfully", data=flag.model_dump())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def update_flag(
        self,
        flag_id: int,
        request: UrlFlagUpdateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            flag = UrlFlagControl.update_flag(current_user, flag_id, request, db)
            return UrlFlagResponse(status=200, message="URL Flag updated successfully", data=flag.model_dump())
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_flag(
        self,
        flag_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            UrlFlagControl.delete_flag(current_user, flag_id, db)
            return BaseResponseModel(status=200, message="URL Flag deleted successfully")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_all_flags(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            flags = UrlFlagControl.get_all_flags(db, skip, limit)
            return UrlFlagListResponse(status=200, message="URL Flags retrieved successfully", data=[f.model_dump() for f in flags])
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_my_flags(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            flags = UrlFlagControl.get_user_flags(current_user, db, skip, limit)
            return UrlFlagListResponse(status=200, message="URL Flags retrieved successfully", data=[f.model_dump() for f in flags])
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_flag_by_id(
        self,
        flag_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            flag = UrlFlagControl.get_flag(flag_id, db)
            return UrlFlagResponse(status=200, message="URL Flag retrieved successfully", data=flag.model_dump())
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
