"""
ML Prediction Service - Handles URL prediction via Redis message queue.
Sends prediction requests to SEMD-ml service and waits for results.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

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
        
        result = ml_service_client.predict_url_sync(
            url=url,
            model_id=str(model_id) if model_id else None,
            timeout=timeout
        )
        
        if result.get('status') == 'timeout':
            raise TimeoutError(f"ML service did not respond within {timeout} seconds")
        
        if result.get('status') == 'failed':
            raise ValueError(result.get('error', 'Prediction failed'))
        
        prediction_data = result.get('prediction', {})
        
        return {
            'url': url,
            'prediction': prediction_data.get('class', 'unknown'),
            'confidence': prediction_data.get('confidence', 0.0),
            'probabilities': prediction_data.get('probabilities', {}),
            'model_id': model_id or 0,
            'model_name': result.get('model_id', 'default'),
            'algorithm': 'unknown'
        }

    async def predict_urls(
        self,
        urls: List[str],
        model_id: Optional[int] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        logger.info(f"Submitting batch prediction job for {len(urls)} URLs")
        
        result = ml_service_client.predict_urls_sync(
            urls=urls,
            model_id=str(model_id) if model_id else None,
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
                    'prediction': pred_data.get('class', 'unknown'),
                    'confidence': pred_data.get('confidence', 0.0),
                    'probabilities': pred_data.get('probabilities', {}),
                    'model_id': model_id or 0,
                    'model_name': r.get('model_id', 'default'),
                    'algorithm': 'unknown'
                })
        
        return {
            'predictions': predictions,
            'total': result.get('total', len(urls)),
            'success_count': result.get('successful', len(predictions)),
            'error_count': result.get('failed', 0),
            'errors': None
        }
