from routers import BaseRoute
from fastapi import HTTPException
from models import PredictionResponse, PredictionRequest
from services.ml_service_client import ml_service_client
from typing import Any, List
import csv
import io
import logging

logger = logging.getLogger(__name__)


class PredictionRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/prediction",
            tags=["prediction"],
            responses={
                404: {"description": "Not found"}, 
                501: {"description": "Not implemented"}, 
                422: {"description": "Validation error"},
                503: {"description": "ML service unavailable"}
            }
        )

        self.router.post(
            "/predict", 
            response_model=PredictionResponse,
            summary="Predict URL",
            description="Predict if a URL is malicious or not using ML service"
        )(self.predict)

    async def predict(self, request: PredictionRequest):
        urls = await self._extract_urls(request)
        
        if not urls:
            raise HTTPException(status_code=422, detail="No URLs provided")

        if len(urls) == 1:
            result = self._predict_single(urls[0])
            return PredictionResponse(data=[result])
        else:
            results = self._predict_batch(urls)
            return PredictionResponse(data=results)

    async def _extract_urls(self, request: PredictionRequest) -> List[str]:
        urls = []
        
        if request.url:
            if isinstance(request.url, str):
                urls = [request.url]
            elif isinstance(request.url, list):
                urls = request.url
        
        if request.text_file:
            content = await request.text_file.read()
            text = content.decode('utf-8')
            file_urls = [line.strip() for line in text.split('\n') if line.strip()]
            urls.extend(file_urls)
        
        if request.csv_file:
            content = await request.csv_file.read()
            text = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                if 'url' in row and row['url'].strip():
                    urls.append(row['url'].strip())
                elif row:
                    first_value = list(row.values())[0].strip()
                    if first_value:
                        urls.append(first_value)
        
        return urls

    def _predict_single(self, url: str) -> dict:
        logger.info(f"Predicting single URL: {url}")
        
        ml_result = ml_service_client.predict_url_sync(url, timeout=30)
        
        if ml_result.get("status") == "timeout":
            raise HTTPException(
                status_code=503, 
                detail="ML service did not respond in time"
            )
        
        if ml_result.get("status") == "failed":
            raise HTTPException(
                status_code=500, 
                detail=ml_result.get("error", "Prediction failed")
            )
        
        return self._format_result(ml_result)

    def _predict_batch(self, urls: List[str]) -> List[dict]:
        logger.info(f"Predicting batch of {len(urls)} URLs")
        
        ml_result = ml_service_client.predict_urls_sync(urls, timeout=60)
        
        if ml_result.get("status") == "timeout":
            raise HTTPException(
                status_code=503, 
                detail="ML service did not respond in time"
            )
        
        if ml_result.get("status") == "failed":
            raise HTTPException(
                status_code=500, 
                detail=ml_result.get("error", "Batch prediction failed")
            )
        
        results = []
        for item in ml_result.get("results", []):
            results.append(self._format_result(item))
        
        return results

    def _format_result(self, ml_result: dict) -> dict:
        prediction = ml_result.get("prediction", {})
        
        return {
            "url": ml_result.get("url", ""),
            "is_malicious": prediction.get("is_malicious", False),
            "confidence": prediction.get("confidence", 0.0),
            "predicted_class": prediction.get("class", "unknown"),
            "suggested_desc": ml_result.get("suggested_desc", ""),
            "job_id": ml_result.get("job_id"),
            "model_id": ml_result.get("model_id")
        }
