from routers import BaseRoute
from fastapi import Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional

from control.service_conf_control import ServiceConfControl
from guard.auth_guard import AuthGuard, get_async_db
from database import User
from models.service_conf_model import ServiceConfModel


class ServiceConfRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/setting/service",
            tags=["service-configuration"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 422: {"description": "Validation error"}}
        )

        self.router.get(
            "/",
            response_model=List[ServiceConfModel],
            summary="List Service Configurations",
            description="Get all service configurations for the current user"
        )(self.list_services)

        self.router.get(
            "/{service_id}",
            response_model=ServiceConfModel,
            summary="Get Service Configuration",
            description="Get a specific service configuration by ID"
        )(self.get_service)

        self.router.post(
            "/{service_id}/activate",
            response_model=ServiceConfModel,
            summary="Activate Service",
            description="Activate a service configuration"
        )(self.activate_service)

        self.router.post(
            "/{service_id}/deactivate",
            response_model=ServiceConfModel,
            summary="Deactivate Service",
            description="Deactivate a service configuration"
        )(self.deactivate_service)

        self.router.get(
            "/active/list",
            response_model=List[ServiceConfModel],
            summary="List Active Services",
            description="Get all active service configurations"
        )(self.list_active_services)

    async def list_services(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ServiceConfControl(db, current_user.user_id)
        services = await control.list_services()
        return [ServiceConfModel.model_validate(s) for s in services]

    async def get_service(
        self,
        service_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ServiceConfControl(db, current_user.user_id)
        service = await control.get_service(service_id)
        return ServiceConfModel.model_validate(service)

    async def activate_service(
        self,
        service_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ServiceConfControl(db, current_user.user_id)
        service = await control.activate_service(service_id)
        return ServiceConfModel.model_validate(service)

    async def deactivate_service(
        self,
        service_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ServiceConfControl(db, current_user.user_id)
        service = await control.deactivate_service(service_id)
        return ServiceConfModel.model_validate(service)

    async def list_active_services(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db),
        service_type: Optional[str] = Query(None, description="Filter by service type")
    ):
        control = ServiceConfControl(db, current_user.user_id)
        services = await control.get_active_services(service_type)
        return [ServiceConfModel.model_validate(s) for s in services]
