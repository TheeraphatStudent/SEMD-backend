from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from database import UsageLog

class UsageLogService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_prediction_usage(
        self,
        service_id: Optional[int] = None,
        access_key_id: Optional[int] = None,
        prediction_id: Optional[int] = None
    ) -> UsageLog:
        usage_log = UsageLog(
            service_id=service_id,
            access_key_id=access_key_id,
            prediction_id=prediction_id,
            type="PREDICT"
        )
        
        self.db.add(usage_log)
        await self.db.commit()
        await self.db.refresh(usage_log)
        
        return usage_log
    
    async def log_access_key_usage(
        self,
        access_key_id: int,
        service_id: Optional[int] = None
    ) -> UsageLog:
        usage_log = UsageLog(
            service_id=service_id,
            access_key_id=access_key_id,
            prediction_id=None,
            type="ACCESS_KEY"
        )
        
        self.db.add(usage_log)
        await self.db.commit()
        await self.db.refresh(usage_log)
        
        return usage_log
    
    async def get_usage_logs_by_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[UsageLog]:
        stmt = (
            select(UsageLog)
            .order_by(UsageLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_usage_logs_by_access_key(
        self,
        access_key_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[UsageLog]:
        stmt = (
            select(UsageLog)
            .where(UsageLog.access_key_id == access_key_id)
            .order_by(UsageLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
