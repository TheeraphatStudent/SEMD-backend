from routers import BaseRoute
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models import PredictionResponse, PredictionRequest
from control.prediction_control import PredictionControl
from guard.auth_guard import AuthGuard, get_async_db
from database import User
from typing import List, Optional
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
            description="Predict if a URL is malicious or not using configured service (ML model or third-party)"
        )(self.predict)

    async def predict(
        self,
        request: PredictionRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        urls = await self._extract_urls(request)
        
        if not urls:
            raise HTTPException(status_code=422, detail="No URLs provided")

        access_key_id = None
        
        control = PredictionControl(db, current_user.user_id, access_key_id, user=current_user)
        
        if request.service_id:
            results = await control.predict(urls, request.service_id)
            return PredictionResponse(
                status=200,
                message="Prediction completed successfully",
                data=results
            )
        else:
            results = await control.predict(urls)
            return PredictionResponse(
                status=200,
                message="Prediction completed successfully",
                data=results
            )

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
