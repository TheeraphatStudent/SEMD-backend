"""Domain 5: proves the SSRF validator is actually wired into BOTH URL-
submission entry points, not just built. `/prediction/predict` goes through
`control/prediction_control.py`; `/ml/predict` and `/ml/predict/batch` go
through `services/ml_prediction_service.py` directly, bypassing
PredictionControl entirely (confirmed by reading routers/ml/ml_route.py) --
a validator wired into only one path would leave the other one exploitable.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from control.prediction_control import PredictionControl
from core.exceptions import ValidationError
from services.ml_prediction_service import MLPredictionService


class FakeAsyncSession:
    async def execute(self, _stmt):
        return SimpleNamespace(scalar_one_or_none=lambda: None)


class PredictionControlSsrfTests(unittest.IsolatedAsyncioTestCase):
    async def test_predict_rejects_loopback_url_before_dispatch(self):
        control = PredictionControl(FakeAsyncSession(), user_id=1, user=SimpleNamespace(user_id=1))
        with patch.object(control.prediction_service, 'predict_with_service', new=AsyncMock()) as dispatch:
            with self.assertRaises(ValidationError) as ctx:
                await control.predict(['http://127.0.0.1/admin'])
        dispatch.assert_not_called()
        self.assertEqual(ctx.exception.code, 'UNSAFE_URL')

    async def test_predict_rejects_cloud_metadata_endpoint(self):
        control = PredictionControl(FakeAsyncSession(), user_id=1, user=SimpleNamespace(user_id=1))
        with patch.object(control.prediction_service, 'predict_with_service', new=AsyncMock()) as dispatch:
            with self.assertRaises(ValidationError):
                await control.predict(['http://169.254.169.254/latest/meta-data/'])
        dispatch.assert_not_called()

    async def test_predict_allows_public_url_through_to_dispatch(self):
        control = PredictionControl(FakeAsyncSession(), user_id=1, user=SimpleNamespace(user_id=1))
        with patch.object(control.prediction_service, 'predict_with_service', new=AsyncMock(return_value=[])) as dispatch, \
             patch.object(control, '_get_default_ml_service', new=AsyncMock(return_value=1)):
            await control.predict(['https://93.184.216.34/'])  # literal public IP, no DNS needed
        dispatch.assert_called_once()


class MLPredictionServiceSsrfTests(unittest.IsolatedAsyncioTestCase):
    async def test_ml_predict_url_rejects_private_ip_before_queueing(self):
        service = MLPredictionService(FakeAsyncSession())
        with patch('services.ml_prediction_service.ml_service_client.predict_url_sync') as mocked:
            with self.assertRaises(ValidationError):
                await service.predict_url('http://192.168.1.1/', model_id=None)
        mocked.assert_not_called()

    async def test_ml_predict_urls_rejects_batch_with_any_unsafe_url(self):
        service = MLPredictionService(FakeAsyncSession())
        with patch('services.ml_prediction_service.ml_service_client.predict_urls_sync') as mocked:
            with self.assertRaises(ValidationError) as ctx:
                await service.predict_urls(['https://93.184.216.34/', 'http://10.0.0.1/'])
        mocked.assert_not_called()
        rejected_urls = {e['url'] for e in ctx.exception.errors}
        self.assertEqual(rejected_urls, {'http://10.0.0.1/'})


if __name__ == '__main__':
    unittest.main()
