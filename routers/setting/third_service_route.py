from routers import BaseRoute
from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from control.third_service_control import ThirdServiceControl
from guard.auth_guard import AuthGuard, get_async_db
from database import User
from models.third_service_model import (
    ThirdServiceCreateRequest,
    ThirdServiceUpdateRequest,
    ThirdServiceExecuteRequest,
    ThirdServiceResponse
)
from models.base_response_model import BaseResponseModel

class ThirdServiceRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/setting/third-service",
            tags=["third-service"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 422: {"description": "Validation error"}}
        )

        self.router.get(
            "/",
            response_model=List[ThirdServiceResponse],
            summary="List Third-Party Services",
            description="List all third-party service configurations for the current user"
        )(self.list_third_services)

        self.router.post(
            "/",
            response_model=ThirdServiceResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create Third-Party Service",
            description="Create a new third-party service configuration"
        )(self.create_third_service)

        self.router.get(
            "/{id}",
            response_model=ThirdServiceResponse,
            summary="Get Third-Party Service",
            description="Retrieve a third-party service configuration by ID"
        )(self.get_third_service)

        self.router.put(
            "/{id}",
            response_model=ThirdServiceResponse,
            summary="Update Third-Party Service",
            description="Update a third-party service configuration"
        )(self.update_third_service)

        self.router.delete(
            "/{id}",
            response_model=BaseResponseModel,
            summary="Delete Third-Party Service",
            description="Soft delete a third-party service (sets is_active=False)"
        )(self.delete_third_service)

        self.router.post(
            "/{id}/execute",
            response_model=Dict[str, Any],
            summary="Execute Third-Party Service",
            description="Execute a third-party service with runtime variables"
        )(self.execute_third_service)

        self.router.post(
            "/{id}/rest-api/test",
            response_model=Dict[str, Any],
            summary="Test Third Service",
            description="Test a third-party service API"
        )(self.test_third_service)

    async def list_third_services(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ThirdServiceControl(db, current_user.user_id)
        return await control.list()

    async def create_third_service(
        self,
        data: ThirdServiceCreateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ThirdServiceControl(db, current_user.user_id)
        return await control.create(data)

    async def get_third_service(
        self,
        id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ThirdServiceControl(db, current_user.user_id)
        return await control.get(id)

    async def update_third_service(
        self,
        id: int,
        data: ThirdServiceUpdateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ThirdServiceControl(db, current_user.user_id)
        return await control.update(id, data)

    async def delete_third_service(
        self,
        id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ThirdServiceControl(db, current_user.user_id)
        await control.delete(id)
        return BaseResponseModel(
            status="success",
            message="Third-party service deleted successfully"
        )

    async def execute_third_service(
        self,
        id: int,
        request: ThirdServiceExecuteRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ThirdServiceControl(db, current_user.user_id)
        return await control.execute(id, request.vars)

    async def test_third_service(
        self,
        id: int,
        request: ThirdServiceExecuteRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ThirdServiceControl(db, current_user.user_id)
        return await control.test_execute(id, request.vars)
