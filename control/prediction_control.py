from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional

from services.prediction_service import PredictionService
from services.usage_log_service import UsageLogService


class PredictionControl:
    def __init__(self, db: AsyncSession, user_id: int = None, access_key_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        self.access_key_id = access_key_id
        self.prediction_service = PredictionService(db)
        self.usage_log_service = UsageLogService(db)
    
    async def predict_with_service(self, service_id: int, urls: List[str]) -> List[Dict[str, Any]]:
        results = await self.prediction_service.predict_with_service(
            service_id=service_id,
            urls=urls,
            user_id=self.user_id
        )
        
        for _ in results:
            await self.usage_log_service.log_prediction_usage(
                service_id=service_id,
                access_key_id=self.access_key_id,
                prediction_id=None
            )
        
        return results
    
    def predict_default(self, url: str) -> Dict[str, Any]:
        return PredictionService.predict_url_default(url)
    
    async def predict_default_async(self, urls: List[str]) -> List[Dict[str, Any]]:
        results = []
        
        for url in urls:
            result = PredictionService.predict_url_default(url)
            results.append(result)
            
            if self.access_key_id:
                await self.usage_log_service.log_prediction_usage(
                    service_id=None,
                    access_key_id=self.access_key_id,
                    prediction_id=None
                )
        
        return results
