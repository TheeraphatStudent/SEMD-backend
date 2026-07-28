from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from datetime import datetime

from models.db import ServiceConf, ThirdServiceConf
from models.service.third_service_model import ThirdServiceCreateRequest, ThirdServiceUpdateRequest


class ThirdServiceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_service_conf(self, user_id: int, service_name: str) -> ServiceConf:
        service_conf = ServiceConf(
            user_id=user_id,
            service_name=service_name,
            service_type='REST_API',
            is_active=True,
            version_no='1.0.0',
            config_uri='',
            config_json={}
        )
        self.db.add(service_conf)
        await self.db.flush()
        await self.db.refresh(service_conf)
        return service_conf

    async def create_third_service(self, user_id: int, data: ThirdServiceCreateRequest) -> ThirdServiceConf:
        service_conf = await self.create_service_conf(user_id, data.service_name)

        third_service = ThirdServiceConf(
            service_conf_id=service_conf.service_conf_id,
            service_name=data.service_name,
            base_url=data.base_url,
            http_method=data.http_method,
            headers_json=data.headers_json,
            config_json=data.config_json,
            mapping_json=data.mapping_json,
            is_active=True
        )

        self.db.add(third_service)
        await self.db.commit()
        await self.db.refresh(third_service)
        return third_service

    async def list_user_services(self, user_id: int) -> list[ThirdServiceConf]:
        stmt = (
            select(ThirdServiceConf)
            .join(ServiceConf, ServiceConf.service_conf_id == ThirdServiceConf.service_conf_id)
            .where(ServiceConf.user_id == user_id)
            .where(ThirdServiceConf.is_active == True)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_third_service(self, id: int) -> ThirdServiceConf:
        stmt = select(ThirdServiceConf).where(
            ThirdServiceConf.third_service_conf_id == id)
        result = await self.db.execute(stmt)
        third_service = result.scalar_one_or_none()

        if not third_service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Third service not found'
            )

        return third_service

    async def get_third_service_by_user(self, user_id: int, id: int) -> ThirdServiceConf:
        stmt = (
            select(ThirdServiceConf)
            .join(ServiceConf, ServiceConf.service_conf_id == ThirdServiceConf.service_conf_id)
            .where(ThirdServiceConf.third_service_conf_id == id)
            .where(ServiceConf.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        third_service = result.scalar_one_or_none()

        if not third_service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Third service not found or access denied'
            )

        return third_service

    async def update_third_service(self, id: int, data: ThirdServiceUpdateRequest) -> ThirdServiceConf:
        third_service = await self.get_third_service(id)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return third_service

        update_data['updated_at'] = datetime.utcnow()

        stmt = (
            update(ThirdServiceConf)
            .where(ThirdServiceConf.third_service_conf_id == id)
            .values(**update_data)
        )
        await self.db.execute(stmt)
        await self.db.commit()
        await self.db.refresh(third_service)

        return third_service

    async def delete_third_service(self, id: int) -> None:
        stmt = (
            update(ThirdServiceConf)
            .where(ThirdServiceConf.third_service_conf_id == id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        result = await self.db.execute(stmt)

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Third service not found'
            )

        await self.db.commit()
