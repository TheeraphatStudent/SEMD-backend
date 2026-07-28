from routers import BaseRoute
from models import BaseResponseModel
from models.service.system_config_model import SystemConfigModel, SystemConfigUpdateRequest
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import Field

from control.system_config_control import SystemConfigControl
from guard.auth_guard import AuthGuard, get_db
from models.db import User
from libs.types.enums import RoleType


class SystemConfigListResponse(BaseResponseModel):
    data: List[SystemConfigModel] = Field(title="data", description="List of system configs")


class SystemConfigResponse(BaseResponseModel):
    data: SystemConfigModel = Field(title="data", description="System config data")


class SystemConfigRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/setting/system-config",
            tags=["system-config"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 403: {"description": "Forbidden"}}
        )

        self.router.get(
            "",
            response_model=SystemConfigListResponse,
            summary="[Admin] Get All System Configs",
            description="Get all system configuration values. Admin only."
        )(self.get_all_configs)
        
        self.router.get(
            "/{config_key}",
            response_model=SystemConfigResponse,
            summary="[Admin] Get System Config by Key",
            description="Get a specific system configuration by key. Admin only."
        )(self.get_config_by_key)
        
        self.router.put(
            "/{config_key}",
            response_model=SystemConfigResponse,
            summary="[Admin] Update System Config",
            description="Update a system configuration value by key. Admin only."
        )(self.update_config)

    def _check_admin_permission(self, user: User):
        if user.role not in [RoleType.ADMIN.value, RoleType.SUPER_ADMIN.value]:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )

    async def get_all_configs(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin_permission(current_user)
        try:
            configs = SystemConfigControl.get_all_configs(db)
            return SystemConfigListResponse(
                status=200,
                message="System configs retrieved successfully",
                data=configs
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_config_by_key(
        self,
        config_key: str,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin_permission(current_user)
        try:
            config = SystemConfigControl.get_config_by_key(config_key, db)
            return SystemConfigResponse(
                status=200,
                message="System config retrieved successfully",
                data=config
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def update_config(
        self,
        config_key: str,
        request: SystemConfigUpdateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        self._check_admin_permission(current_user)
        try:
            config = SystemConfigControl.update_config_by_key(config_key, request, db)
            return SystemConfigResponse(
                status=200,
                message="System config updated successfully",
                data=config
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
