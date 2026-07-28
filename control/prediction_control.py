from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import reject_unsafe_urls
from models.db import ServiceConf, User
from libs.types.enums import ServiceType
from services.prediction_service import PredictionService
from services.queue_service import QueueService
from services.url_flag_service import UrlFlagService
from services.usage_log_service import UsageLogService


class PredictionControl:
    def __init__(self, db: AsyncSession, user_id: int = None, access_key_id: Optional[int] = None, user: Optional[User] = None):
        self.db = db
        self.user_id = user_id
        self.access_key_id = access_key_id
        self.user = user
        self.prediction_service = PredictionService(db)
        self.usage_log_service = UsageLogService(db)

    async def predict(self, urls: List[str], service_id: Optional[int] = None) -> List[Dict[str, Any]]:
        await reject_unsafe_urls(urls)

        if not service_id:
            service_id = await self._get_default_ml_service()
            if not service_id:
                raise HTTPException(
                    status_code=400,
                    detail="No service_id provided and no default ML service found. Please configure an ML service or provide a service_id."
                )
        
        results = await self.prediction_service.predict_with_service(
            service_id=service_id,
            urls=urls,
            user_id=self.user_id
        )

        for result in results:
            prediction_id = result.get('prediction_id')
            await self.usage_log_service.log_prediction_usage(
                service_id=service_id,
                access_key_id=self.access_key_id,
                prediction_id=prediction_id
            )

            url = result.get('url')
            flag_info = await self._check_url_flag(url)
            result['is_flag'] = flag_info['is_flag']
            if flag_info['is_flag']:
                result['flag_type'] = flag_info['flag_type']
                result['flag_id'] = flag_info['flag_id']

            QueueService.add_to_retrain_queue(url, self.user)

        return results

    async def _get_default_ml_service(self) -> Optional[int]:
        stmt = select(ServiceConf).where(
            ServiceConf.is_active == True,
            ServiceConf.service_type == ServiceType.ML_MODEL.value
        ).order_by(ServiceConf.created_at.asc()).limit(1)
        
        result = await self.db.execute(stmt)
        service = result.scalar_one_or_none()
        
        return service.service_conf_id if service else None

    async def _check_url_flag(self, url: str) -> Dict[str, Any]:
        flag = await UrlFlagService.check_url_flag_async(url, self.user_id, self.db)

        if flag:
            return {
                'is_flag': True,
                'flag_type': flag.type,
                'flag_id': flag.url_flag_id
            }

        return {'is_flag': False}
