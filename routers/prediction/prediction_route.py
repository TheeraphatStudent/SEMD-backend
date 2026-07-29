from routers import BaseRoute
from fastapi import HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from models import PredictionResponse, PredictionRequest
from control.prediction_control import PredictionControl
from guard.auth_guard import AuthGuard, get_async_db
from models.db import User
from typing import List, Optional
import csv
import io
import logging

from config.settings import settings
from services.prediction_rate_limiter import (
    PredictionRateLimiter,
    RateLimiterUnavailableError,
)

logger = logging.getLogger(__name__)


class PredictionRoute(BaseRoute):
    def __init__(self, rate_limiter: Optional[PredictionRateLimiter] = None):
        self.rate_limiter = rate_limiter or PredictionRateLimiter(
            max_requests=settings.prediction_rate_limit_requests,
            window_seconds=settings.prediction_rate_limit_window_seconds,
        )
        super().__init__(
            prefix='/prediction',
            tags=['prediction'],
            responses={
                404: {'description': 'Not found'},
                501: {'description': 'Not implemented'},
                422: {'description': 'Validation error'},
                503: {'description': 'ML service unavailable'}
            }
        )

        self.router.post(
            '/predict',
            response_model=PredictionResponse,
            summary='Predict URL',
            description='Predict if a URL is malicious or not using configured service (ML model or third-party). '
                        'No login required -- an expired, missing, or invalid token degrades to an anonymous call '
                        'instead of a 401, so the browser extension can call this without a session.'
        )(self.predict)

    async def predict(
        self,
        request: PredictionRequest,
        http_request: Request,
        current_user: Optional[User] = Depends(
            AuthGuard.get_current_user_optional),
        db: AsyncSession = Depends(get_async_db)
    ):
        if current_user is None:
            client_identifier = http_request.client.host if http_request.client else 'unknown'
            try:
                limit = self.rate_limiter.check(client_identifier)
            except RateLimiterUnavailableError:
                logger.error(
                    'anonymous prediction rate limiter unavailable',
                    extra={'request_id': getattr(
                        http_request.state, 'request_id', None)},
                )
                raise HTTPException(
                    status_code=503,
                    detail='Prediction service temporarily unavailable. Please retry later.',
                )
            if not limit.allowed:
                logger.warning(
                    'anonymous prediction rate limit exceeded',
                    extra={'request_id': getattr(
                        http_request.state, 'request_id', None)},
                )
                raise HTTPException(
                    status_code=429,
                    detail='Too many prediction requests. Please retry later.',
                    headers={'Retry-After': str(limit.retry_after_seconds)},
                )

        urls = await self._extract_urls(request)

        if not urls:
            raise HTTPException(status_code=422, detail='No URLs provided')

        access_key_id = None
        user_id = current_user.user_id if current_user else None

        control = PredictionControl(
            db, user_id, access_key_id, user=current_user)

        results = await control.predict(urls, request.service_id)
        return PredictionResponse(
            status=200,
            message='Prediction completed successfully',
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
            file_urls = [line.strip()
                         for line in text.split('\n') if line.strip()]
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
