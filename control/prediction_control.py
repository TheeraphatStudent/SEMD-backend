from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional

from services.prediction_service import PredictionService
from services.usage_log_service import UsageLogService
from services.url_flag_service import UrlFlagService
from services.queue_service import QueueService
from database import User

class PredictionControl:
    def __init__(self, db: AsyncSession, user_id: int = None, access_key_id: Optional[int] = None, user: Optional[User] = None):
        self.db = db
        self.user_id = user_id
        self.access_key_id = access_key_id
        self.user = user
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
                
                url = result.get('url')
                flag_info = await self._check_url_flag(url)
                result['is_flag'] = flag_info['is_flag']
                if flag_info['is_flag']:
                    result['flag_type'] = flag_info['flag_type']
                    result['flag_id'] = flag_info['flag_id']
                
                QueueService.add_to_retrain_queue(url, self.user)
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
                
                flag_info = await self._check_url_flag(url)
                
                result = {
                    "id": str(prediction_record.prediction_id),
                    "url": url,
                    "prediction_id": prediction_record.prediction_id,
                    "result": mock_result,
                    "is_flag": flag_info['is_flag']
                }
                
                if flag_info['is_flag']:
                    result['flag_type'] = flag_info['flag_type']
                    result['flag_id'] = flag_info['flag_id']
                
                results.append(result)
                
                await self.usage_log_service.log_prediction_usage(
                    service_id=None,
                    access_key_id=self.access_key_id,
                    prediction_id=prediction_record.prediction_id
                )

                QueueService.add_to_retrain_queue(url, self.user)
        
        return results
    
    async def _check_url_flag(self, url: str) -> Dict[str, Any]:
        flag = await UrlFlagService.check_url_flag_async(url, self.user_id, self.db)
        
        if flag:
            return {
                'is_flag': True,
                'flag_type': flag.type,
                'flag_id': flag.url_flag_id
            }
        
        return {'is_flag': False}