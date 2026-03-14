from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from services.third_service_service import ThirdServiceService
from services.client.third_service_executor import ThirdServiceExecutor
from models.third_service_model import (
    ThirdServiceCreateRequest,
    ThirdServiceUpdateRequest,
    ThirdServiceResponse
)
from database import ThirdServiceConf

class ThirdServiceControl:
    def __init__(self, db: AsyncSession, user_id: int):
        self.service = ThirdServiceService(db)
        self.user_id = user_id
    
    async def list(self) -> List[ThirdServiceResponse]:
        services = await self.service.list_user_services(self.user_id)
        return [ThirdServiceResponse.model_validate(s) for s in services]
    
    async def create(self, data: ThirdServiceCreateRequest) -> ThirdServiceResponse:
        third_service = await self.service.create_third_service(self.user_id, data)
        return ThirdServiceResponse.model_validate(third_service)
    
    async def get(self, id: int) -> ThirdServiceResponse:
        third_service = await self.service.get_third_service_by_user(self.user_id, id)
        return ThirdServiceResponse.model_validate(third_service)
    
    async def update(self, id: int, data: ThirdServiceUpdateRequest) -> ThirdServiceResponse:
        await self.service.get_third_service_by_user(self.user_id, id)
        third_service = await self.service.update_third_service(id, data)
        return ThirdServiceResponse.model_validate(third_service)
    
    async def delete(self, id: int) -> None:
        await self.service.get_third_service_by_user(self.user_id, id)
        await self.service.delete_third_service(id)
    
    async def execute(self, id: int, vars: Dict[str, Any]) -> Dict[str, Any]:
        conf = await self.service.get_third_service_by_user(self.user_id, id)
        
        if not conf.is_active:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Third service is not active"
            )
        
        executor = ThirdServiceExecutor(conf)
        return await executor.execute(vars)
    
    async def test_execute(self, id: int, vars: Dict[str, Any]) -> Dict[str, Any]:
        conf = await self.service.get_third_service_by_user(self.user_id, id)
        
        if not conf.is_active:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Third service is not active"
            )
        
        executor = ThirdServiceExecutor(conf)
        result = await executor.execute(vars)
        
        return {
            "test_result": result,
            "service_name": conf.service_name,
            "url": conf.base_url,
            "method": conf.http_method,
            "vars_used": vars
        }
