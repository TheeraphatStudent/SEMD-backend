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
    
    async def predict(self, urls: List[str], service_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if service_id:
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
        else:
            results = []
            
            for url in urls:
                mock_result = PredictionService.generate_mock_prediction(url)
                
                prediction_record = await self.prediction_service.prediction_storage.create_prediction_record(
                    user_id=self.user_id,
                    url=url,
                    prediction_result=mock_result,
                    mapping_json={
                        "is_malicious": "is_malicious",
                        "class": "class",
                        "suggested_desc": "suggested"
                    }
                )
                
                result = {
                    "id": str(prediction_record.prediction_id),
                    "url": url,
                    "prediction_id": prediction_record.prediction_id,
                    "result": mock_result
                }
                results.append(result)
                
                await self.usage_log_service.log_prediction_usage(
                    service_id=None,
                    access_key_id=self.access_key_id,
                    prediction_id=prediction_record.prediction_id
                )
        
        return results