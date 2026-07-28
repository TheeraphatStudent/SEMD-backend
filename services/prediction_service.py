"""
Prediction service - Business logic for URL prediction.
Supports both ML model and third-party service predictions.
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import ServiceConf, ThirdServiceConf
from libs.types.enums import ServiceType
from services.client.third_service_executor import ThirdServiceExecutor
from services.prediction_storage_service import PredictionStorageService


class PredictionService:

    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.prediction_storage = PredictionStorageService(db)

    async def predict_with_service(
        self,
        service_id: int,
        urls: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        from models.db import User
        from libs.types.enums import RoleType
        
        stmt = select(ServiceConf).where(
            ServiceConf.service_conf_id == service_id,
            ServiceConf.is_active == True
        )
        result = await self.db.execute(stmt)
        service_conf = result.scalar_one_or_none()

        if not service_conf:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service configuration {service_id} not found or inactive"
            )

        if user_id and service_conf.user_id and service_conf.user_id != user_id:
            owner_stmt = select(User).where(User.user_id == service_conf.user_id)
            owner_result = await self.db.execute(owner_stmt)
            owner = owner_result.scalar_one_or_none()
            
            if not owner or owner.role not in [RoleType.ADMIN.value, RoleType.SUPER_ADMIN.value]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='Access denied to this service configuration'
                )

        conf_id = service_conf.service_conf_id
        conf_name = service_conf.service_name
        conf_type = service_conf.service_type

        if conf_type == ServiceType.ML_MODEL.value:
            return await self._predict_with_ml_model(conf_id, conf_name, conf_type, urls, user_id)
        elif conf_type == ServiceType.REST_API.value:
            return await self._predict_with_third_party(conf_id, conf_name, conf_type, urls, user_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported service type: {conf_type}"
            )

    async def _predict_with_ml_model(
        self,
        service_conf_id: int,
        service_name: str,
        service_type: str,
        urls: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        from services.ml_service_client import ml_service_client

        results = []
        for url in urls:
            ml_result = await ml_service_client.predict_url_sync(url, timeout=30)

            if ml_result.get('status') == 'timeout':
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail='ML service did not respond in time'
                )

            if ml_result.get('status') == 'failed':
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ml_result.get('error', 'Prediction failed')
                )

            prediction_data = ml_result.get('prediction', {})
            prediction_record = await self.prediction_storage.create_prediction_record(
                user_id=user_id,
                url=url,
                prediction_result={
                    'class': prediction_data.get('prediction', prediction_data.get('class', 'unknown')),
                    'is_malicious': prediction_data.get('is_malicious', False),
                    'accuracy_score': prediction_data.get('confidence', 0),
                    'suggested_desc': ml_result.get('suggested_desc', '')
                },
                mapping_json={
                    'class': 'class',
                    'is_malicious': 'is_malicious',
                    'accuracy_score': 'accuracy_score',
                    'suggested_desc': 'suggested_desc'
                }
            )

            results.append({
                'url': url,
                'service_id': service_conf_id,
                'service_name': service_name,
                'service_type': service_type,
                'prediction_id': prediction_record.prediction_id,
                **ml_result
            })

        return results

    async def _predict_with_third_party(
        self,
        service_conf_id: int,
        service_name: str,
        service_type: str,
        urls: List[str],
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        stmt = select(ThirdServiceConf).where(
            ThirdServiceConf.service_conf_id == service_conf_id,
            ThirdServiceConf.is_active == True
        )
        result = await self.db.execute(stmt)
        third_service = result.scalar_one_or_none()

        if not third_service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Third-party service configuration not found'
            )

        third_service_id = third_service.third_service_conf_id
        third_service_name = third_service.service_name
        config_json = third_service.config_json
        mapping_json = third_service.mapping_json

        executor = ThirdServiceExecutor(third_service)
        results = []

        for url in urls:
            runtime_vars = self._build_runtime_vars(url, config_json)
            prediction_result = await executor.execute(runtime_vars)

            prediction_record = await self.prediction_storage.create_prediction_record(
                user_id=user_id,
                url=url,
                prediction_result=prediction_result,
                mapping_json=mapping_json
            )

            results.append({
                'url': url,
                'service_id': service_conf_id,
                'service_name': service_name,
                'service_type': service_type,
                'third_service_id': third_service_id,
                'third_service_name': third_service_name,
                'prediction_id': prediction_record.prediction_id,
                'result': prediction_result
            })

        return results

    def _build_runtime_vars(self, url: str, config_json: dict) -> Dict[str, Any]:
        vars_dict = {'url': url}

        body_template = config_json.get('body_template', [])
        for mapping in body_template:
            input_key = mapping.get('input')
            if input_key and input_key not in vars_dict:
                if input_key in ['url', 'url_key', 'target_url']:
                    vars_dict[input_key] = url

        url_template = config_json.get('url_template', {})
        query_params = url_template.get('query_params', {})
        for param_name, var_name in query_params.items():
            if var_name not in vars_dict:
                if var_name in ['url', 'url_key', 'target_url']:
                    vars_dict[var_name] = url

        return vars_dict


prediction_service = PredictionService()
