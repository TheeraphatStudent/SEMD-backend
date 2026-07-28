"""
ML Prediction Service - Handles URL prediction via Redis message queue.
Sends prediction requests to SEMD-ml service and waits for results.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import reject_unsafe_urls
from models.db import ModelRegistry
from services.ml_service_client import ml_service_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLPredictionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def predict_url(
        self,
        url: str,
        model_id: Optional[int] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        logger.info(f"Submitting prediction job for URL: {url}")
        await reject_unsafe_urls([url])
        model_selector = await self._resolve_model_selector(model_id)
        
        result = await ml_service_client.predict_url_sync(
            url=url,
            model_id=model_selector,
            timeout=timeout
        )
        
        if result.get('status') == 'timeout':
            raise TimeoutError(f"ML service did not respond within {timeout} seconds")
        
        if result.get('status') == 'failed':
            raise ValueError(result.get('error', 'Prediction failed'))
        
        prediction_data = result.get('prediction', {})
        
        return {
            'url': url,
            'prediction': prediction_data.get('prediction', 'unknown'),
            'is_malicious': prediction_data.get('is_malicious', False),
            'confidence': prediction_data.get('confidence', 0.0),
            'probabilities': prediction_data.get('probabilities', {}),
            'model_id': model_id or 0,
            'model_name': prediction_data.get('model_name', 'default'),
            'model_version': prediction_data.get('model_version', ''),
            'model_alias': prediction_data.get('model_alias', 'champion'),
            'feature_schema_version': prediction_data.get('feature_schema_version', ''),
            'prediction_time_ms': prediction_data.get('prediction_time_ms', 0.0),
            'algorithm': 'unknown',
        }

    async def predict_urls(
        self,
        urls: List[str],
        model_id: Optional[int] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        logger.info(f"Submitting batch prediction job for {len(urls)} URLs")
        await reject_unsafe_urls(urls)
        model_selector = await self._resolve_model_selector(model_id)
        
        result = await ml_service_client.predict_urls_sync(
            urls=urls,
            model_id=model_selector,
            timeout=timeout
        )
        
        if result.get('status') == 'timeout':
            raise TimeoutError(f"ML service did not respond within {timeout} seconds")
        
        if result.get('status') == 'failed':
            raise ValueError(result.get('error', 'Batch prediction failed'))
        
        predictions = []
        results_data = result.get('results', [])
        
        for r in results_data:
            if r.get('status') == 'success':
                pred_data = r.get('prediction', {})
                predictions.append({
                    'url': r.get('url', ''),
                    'prediction': pred_data.get('prediction', 'unknown'),
                    'is_malicious': pred_data.get('is_malicious', False),
                    'confidence': pred_data.get('confidence', 0.0),
                    'probabilities': pred_data.get('probabilities', {}),
                    'model_id': model_id or 0,
                    'model_name': pred_data.get('model_name', 'default'),
                    'model_version': pred_data.get('model_version', ''),
                    'model_alias': pred_data.get('model_alias', 'champion'),
                    'feature_schema_version': pred_data.get('feature_schema_version', ''),
                    'prediction_time_ms': pred_data.get('prediction_time_ms', 0.0),
                    'algorithm': 'unknown',
                })
        
        return {
            'predictions': predictions,
            'total': result.get('total', len(urls)),
            'success_count': result.get('successful', len(predictions)),
            'error_count': result.get('failed', 0),
            'errors': None
        }

    async def _resolve_model_selector(self, model_id: Optional[int]) -> Optional[str]:
        if model_id is None:
            return None

        stmt = select(ModelRegistry).where(ModelRegistry.model_registry_id == model_id)
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Model registry entry {model_id} was not found")
        if model.mlflow_model_version is None:
            raise ValueError(f"Model registry entry {model_id} does not have an MLflow model version")
        return str(model.mlflow_model_version)
