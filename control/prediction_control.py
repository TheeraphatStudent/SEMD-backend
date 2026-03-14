from sqlalchemy.orm import Session
from typing import Dict, Any, List

from services.prediction_service import PredictionService


class PredictionControl:
    def __init__(self, db: Session, user_id: int = None):
        self.db = db
        self.user_id = user_id
        self.prediction_service = PredictionService(db)
    
    async def predict_with_service(self, service_id: int, urls: List[str]) -> List[Dict[str, Any]]:
        return await self.prediction_service.predict_with_service(
            service_id=service_id,
            urls=urls,
            user_id=self.user_id
        )
    
    def predict_default(self, url: str) -> Dict[str, Any]:
        return PredictionService.predict_url_default(url)
