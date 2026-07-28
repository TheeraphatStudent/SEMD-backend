from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from datetime import datetime
from typing import List, Optional

from models.db import ServiceConf, ThirdServiceConf, ModelRegistry
from libs.types.enums import ServiceType


class ServiceConfService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_services(self, user_id: int) -> List[ServiceConf]:
        stmt = select(ServiceConf).where(ServiceConf.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_service_by_id(self, service_id: int, user_id: int = None) -> ServiceConf:
        stmt = select(ServiceConf).where(
            ServiceConf.service_conf_id == service_id)

        if user_id:
            stmt = stmt.where(ServiceConf.user_id == user_id)

        result = await self.db.execute(stmt)
        service = result.scalar_one_or_none()

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Service configuration not found'
            )

        return service

    async def toggle_service_active(self, service_id: int, user_id: int, is_active: bool) -> ServiceConf:
        service = await self.get_service_by_id(service_id, user_id)

        service.is_active = is_active
        service.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(service)

        return service

    async def get_active_services(self, user_id: int = None, service_type: Optional[str] = None) -> List[ServiceConf]:
        stmt = select(ServiceConf).where(ServiceConf.is_active == True)

        if user_id:
            stmt = stmt.where(ServiceConf.user_id == user_id)

        if service_type:
            stmt = stmt.where(ServiceConf.service_type == service_type)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
