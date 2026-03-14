from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from decimal import Decimal

from database import Prediction
from libs.shared import is_class_malicious, normalize_class_name, map_prediction_class

class PredictionStorageService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_prediction_record(
        self,
        user_id: Optional[int],
        url: str,
        prediction_result: Dict[str, Any],
        mapping_json: Dict[str, str] = None
    ) -> Prediction:
        mapped_data = self._map_prediction_result(prediction_result, mapping_json or {})
        
        class_name = mapped_data.get('class')
        is_malicious_mapped = mapped_data.get('is_malicious')
        
        if class_name is not None and is_malicious_mapped is not None:
            normalized_class = normalize_class_name(class_name)
            is_malicious = is_malicious_mapped
        else:
            prediction_value = (
                mapped_data.get('prediction') or 
                mapped_data.get('class') or 
                prediction_result.get('prediction') or 
                prediction_result.get('class') or
                'unknown'
            )
            is_malicious, normalized_class = map_prediction_class(str(prediction_value))
        
        prediction = Prediction(
            user_id=user_id,
            url=url,
            accuracy_score=mapped_data.get('accuracy_score'),
            recall_score=mapped_data.get('recall_score'),
            precision_score=mapped_data.get('precision_score'),
            f1_score=mapped_data.get('f1_score'),
            is_malicious=is_malicious,
            predict_class=normalized_class,
            suggested_desc=mapped_data.get('suggested_desc')
        )
        
        self.db.add(prediction)
        await self.db.commit()
        await self.db.refresh(prediction)
        
        return prediction
    
    def _map_prediction_result(
        self, 
        prediction_result: Dict[str, Any], 
        mapping_json: Dict[str, str]
    ) -> Dict[str, Any]:
        mapped_data = {}
        
        for field_name, json_path in mapping_json.items():
            try:
                value = self._extract_value_by_path(prediction_result, json_path)
                
                if field_name in ['accuracy_score', 'recall_score', 'precision_score', 'f1_score']:
                    if value is not None:
                        mapped_data[field_name] = Decimal(str(value))
                elif field_name == 'suggested_desc':
                    if value is not None:
                        mapped_data[field_name] = str(value)[:512]
                elif field_name == 'is_malicious':
                    if value is not None:
                        if isinstance(value, bool):
                            mapped_data[field_name] = value
                        elif isinstance(value, str):
                            mapped_data[field_name] = value.lower() in ['true', '1', 'yes', 'malicious', 'phishing', 'spam', 'scam']
                        else:
                            mapped_data[field_name] = bool(value)
                elif field_name == 'class':
                    if value is not None:
                        mapped_data[field_name] = str(value)
                else:
                    mapped_data[field_name] = value
                    
            except (KeyError, ValueError, TypeError) as e:
                continue
        
        return mapped_data
    
    def _extract_value_by_path(self, data: Dict[str, Any], path: str) -> Any:
        if not path:
            return None
            
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
                
        return current
