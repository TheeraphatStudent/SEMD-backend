from __future__ import annotations

import json
import logging
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from redis.exceptions import RedisError

from control.prediction_control import PredictionControl
from core.logging import JsonFormatter
from guard.auth_guard import AuthGuard, get_async_db
from routers.prediction.prediction_route import PredictionRoute
from services.ml_prediction_service import MLPredictionService
from services.prediction_rate_limiter import PredictionRateLimiter


class FakeRedis:
    def __init__(self):
        self.values: dict[str, int] = {}
        self.expirations: dict[str, int] = {}

    def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def expire(self, key: str, seconds: int) -> None:
        self.expirations[key] = seconds

    def ttl(self, key: str) -> int:
        return self.expirations.get(key, -1)


class UnavailableRedis:
    def incr(self, _key: str) -> int:
        raise RedisError('Redis unavailable')


class FakeAsyncSession:
    async def execute(self, _statement):
        class Result:
            @staticmethod
            def scalar_one_or_none():
                return None

        return Result()


class PredictionRateLimiterTests(unittest.TestCase):
    def test_blocks_anonymous_burst_after_configured_limit(self):
        limiter = PredictionRateLimiter(
            FakeRedis(), max_requests=2, window_seconds=60)

        self.assertTrue(limiter.check('198.51.100.24').allowed)
        self.assertTrue(limiter.check('198.51.100.24').allowed)
        blocked = limiter.check('198.51.100.24')

        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.retry_after_seconds, 60)

    def test_does_not_store_raw_client_address_in_redis_key(self):
        redis = FakeRedis()
        limiter = PredictionRateLimiter(
            redis, max_requests=1, window_seconds=60)

        limiter.check('198.51.100.24')

        key = next(iter(redis.values))
        self.assertNotIn('198.51.100.24', key)
        self.assertTrue(key.startswith('prediction-rate-limit:'))

    def test_fails_closed_when_redis_is_unavailable(self):
        limiter = PredictionRateLimiter(
            UnavailableRedis(), max_requests=2, window_seconds=60)

        with self.assertRaises(RuntimeError):
            limiter.check('198.51.100.24')


class PredictionLogRedactionTests(unittest.TestCase):
    def test_formatter_removes_urls_from_message_and_extra_fields(self):
        logger = logging.getLogger('prediction-test')
        record = logger.makeRecord(
            logger.name,
            logging.INFO,
            __file__,
            1,
            'submitted https://user:secret@example.com/path?token=abc',
            (),
            None,
            extra={
                'url': 'https://user:secret@example.com/path?token=abc',
                'urls': ['https://example.org/private'],
                'request_id': 'request-1',
            },
        )

        payload = json.loads(JsonFormatter().format(record))

        self.assertNotIn('https://', json.dumps(payload))
        self.assertEqual(payload['url'], '[REDACTED_URL]')
        self.assertEqual(payload['urls'], '[REDACTED_URLS:1]')
        self.assertEqual(payload['request_id'], 'request-1')

    def test_ml_prediction_log_message_does_not_include_submitted_url(self):
        logger = logging.getLogger('services.ml_prediction_service')
        captured = []

        class Capture(logging.Handler):
            def emit(self, record):
                captured.append(record.getMessage())

        handler = Capture()
        logger.addHandler(handler)
        try:
            service = MLPredictionService(FakeAsyncSession())
            with patch(
                'services.ml_prediction_service.ml_service_client.predict_url_sync',
                return_value={'status': 'failed', 'error': 'upstream failed'},
            ):
                with self.assertRaises(ValueError):
                    import asyncio
                    asyncio.run(service.predict_url(
                        'https://example.com/private', model_id=None))
        finally:
            logger.removeHandler(handler)

        self.assertTrue(captured)
        self.assertNotIn('https://example.com/private', '\n'.join(captured))


class PredictionRouteRateLimitTests(unittest.TestCase):
    def setUp(self):
        self._build_client(PredictionRateLimiter(
            FakeRedis(), max_requests=2, window_seconds=60))

    def _build_client(self, limiter):
        self.app = FastAPI()
        self.app.include_router(
            PredictionRoute(rate_limiter=limiter).get_router()
        )
        self.app.dependency_overrides[AuthGuard.get_current_user_optional] = lambda: None

        async def fake_db():
            yield object()

        self.app.dependency_overrides[get_async_db] = fake_db
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.client.close()

    def test_anonymous_burst_receives_rate_limit_rejection(self):
        with patch.object(PredictionControl, 'predict', new=AsyncMock(return_value=[])) as predict:
            responses = [
                self.client.post(
                    '/prediction/predict',
                    json={'url': 'https://example.com', 'service_id': 1},
                )
                for _ in range(3)
            ]

        self.assertEqual(
            [response.status_code for response in responses], [200, 200, 429])
        self.assertEqual(responses[-1].headers['Retry-After'], '60')
        self.assertEqual(predict.await_count, 2)

    def test_anonymous_request_gets_503_when_limiter_is_unavailable(self):
        self.client.close()
        self._build_client(PredictionRateLimiter(
            UnavailableRedis(), max_requests=2, window_seconds=60))

        response = self.client.post(
            '/prediction/predict',
            json={'url': 'https://example.com', 'service_id': 1},
        )

        self.assertEqual(response.status_code, 503)


if __name__ == '__main__':
    unittest.main()
