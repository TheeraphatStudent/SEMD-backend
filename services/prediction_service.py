"""
Prediction service - Business logic for URL prediction.
Supports both ML model and third-party service predictions.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from database import ServiceConf, ThirdServiceConf
from services.client.third_service_executor import ThirdServiceExecutor
from libs.types.enums import ServiceType


class PredictionService:
    
    def __init__(self, db: Session = None):
        self.db = db
    
    async def predict_with_service(
        self, 
        service_id: int, 
        urls: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        service_conf = self.db.query(ServiceConf).filter(
            ServiceConf.service_conf_id == service_id,
            ServiceConf.is_active == True
        ).first()
        
        if not service_conf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service configuration {service_id} not found or inactive"
            )
        
        if user_id and service_conf.user_id and service_conf.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this service configuration"
            )
        
        if service_conf.service_type == ServiceType.ML_MODEL.value:
            return await self._predict_with_ml_model(service_conf, urls)
        elif service_conf.service_type == ServiceType.REST_API.value:
            return await self._predict_with_third_party(service_conf, urls)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported service type: {service_conf.service_type}"
            )
    
    async def _predict_with_ml_model(
        self, 
        service_conf: ServiceConf, 
        urls: List[str]
    ) -> List[Dict[str, Any]]:
        from services.ml_service_client import ml_service_client
        
        results = []
        for url in urls:
            ml_result = ml_service_client.predict_url_sync(url, timeout=30)
            
            if ml_result.get("status") == "timeout":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="ML service did not respond in time"
                )
            
            if ml_result.get("status") == "failed":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ml_result.get("error", "Prediction failed")
                )
            
            results.append({
                "url": url,
                "service_id": service_conf.service_conf_id,
                "service_name": service_conf.service_name,
                "service_type": service_conf.service_type,
                **ml_result
            })
        
        return results
    
    async def _predict_with_third_party(
        self, 
        service_conf: ServiceConf, 
        urls: List[str]
    ) -> List[Dict[str, Any]]:
        third_service = self.db.query(ThirdServiceConf).filter(
            ThirdServiceConf.service_conf_id == service_conf.service_conf_id,
            ThirdServiceConf.is_active == True
        ).first()
        
        if not third_service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Third-party service configuration not found"
            )
        
        executor = ThirdServiceExecutor(third_service)
        results = []
        
        for url in urls:
            runtime_vars = self._build_runtime_vars(url, third_service.config_json)
            result = await executor.execute(runtime_vars)
            
            results.append({
                "url": url,
                "service_id": service_conf.service_conf_id,
                "service_name": service_conf.service_name,
                "service_type": service_conf.service_type,
                "third_service_id": third_service.third_service_conf_id,
                "third_service_name": third_service.service_name,
                "result": result
            })
        
        return results
    
    def _build_runtime_vars(self, url: str, config_json: dict) -> Dict[str, Any]:
        vars_dict = {"url": url}
        
        body_template = config_json.get("body_template", [])
        for mapping in body_template:
            input_key = mapping.get("input")
            if input_key and input_key not in vars_dict:
                if input_key in ["url", "url_key", "target_url"]:
                    vars_dict[input_key] = url
        
        url_template = config_json.get("url_template", {})
        query_params = url_template.get("query_params", {})
        for param_name, var_name in query_params.items():
            if var_name not in vars_dict:
                if var_name in ["url", "url_key", "target_url"]:
                    vars_dict[var_name] = url
        
        return vars_dict
    
    @classmethod
    def generate_mock_prediction(cls, url: str) -> dict:
        is_malicious = "true" if "malicious" in url.lower() else "false"
        accuracy = 0.95 if is_malicious == "true" else 0.87
        suggested = "block" if is_malicious == "true" else "safe"

        return {
            "is_malicious": is_malicious,
            "accuracy": accuracy,
            "suggested": suggested,
        }

    @classmethod
    def predict_url_default(cls, url: str) -> dict:
        prediction_id = str(uuid.uuid4())
        prediction_result = cls.generate_mock_prediction(url)
        
        return {
            "id": prediction_id,
            "url": url,
            "result": prediction_result,
        }


prediction_service = PredictionService()
