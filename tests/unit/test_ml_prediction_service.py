from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.ml_prediction_service import MLPredictionService


class FakeAsyncSession:
    def __init__(self, model_version: int | None):
        self.model_version = model_version

    async def execute(self, _stmt):
        model = None
        if self.model_version is not None:
            model = SimpleNamespace(model_registry_id=7, mlflow_model_version=self.model_version)
        return SimpleNamespace(scalar_one_or_none=lambda: model)


class MLPredictionServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_predict_url_maps_backend_contract_and_model_selector(self):
        service = MLPredictionService(FakeAsyncSession(model_version=12))
        payload = {
            "status": "success",
            "prediction": {
                "url": "https://example.com",
                "prediction": "benign",
                "is_malicious": False,
                "confidence": 0.94,
                "model_name": "semd-malicious-url-detector",
                "model_version": "12",
                "model_alias": "champion",
                "feature_schema_version": "2.1.0",
                "prediction_time_ms": 14.2,
            },
        }

        with patch("services.ml_prediction_service.ml_service_client.predict_url_sync", return_value=payload) as mocked:
            result = await service.predict_url("https://example.com", model_id=7)

        mocked.assert_called_once_with(url="https://example.com", model_id="12", timeout=30)
        self.assertEqual(result["prediction"], "benign")
        self.assertFalse(result["is_malicious"])
        self.assertEqual(result["model_version"], "12")
        self.assertEqual(result["model_alias"], "champion")
        self.assertEqual(result["feature_schema_version"], "2.1.0")

    async def test_predict_urls_maps_batch_contract(self):
        service = MLPredictionService(FakeAsyncSession(model_version=None))
        payload = {
            "status": "success",
            "results": [
                {
                    "status": "success",
                    "url": "https://example.com",
                    "prediction": {
                        "prediction": "benign",
                        "is_malicious": False,
                        "confidence": 0.94,
                        "model_name": "semd-malicious-url-detector",
                        "model_version": "12",
                        "model_alias": "champion",
                        "feature_schema_version": "2.1.0",
                        "prediction_time_ms": 14.2,
                    },
                }
            ],
            "total": 1,
            "successful": 1,
            "failed": 0,
        }

        with patch("services.ml_prediction_service.ml_service_client.predict_urls_sync", return_value=payload):
            result = await service.predict_urls(["https://example.com"])

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["predictions"][0]["model_alias"], "champion")
        self.assertEqual(result["predictions"][0]["prediction_time_ms"], 14.2)

    async def test_missing_model_version_fails_loudly(self):
        service = MLPredictionService(FakeAsyncSession(model_version=None))
        with self.assertRaises(ValueError):
            await service.predict_url("https://example.com", model_id=7)


if __name__ == "__main__":
    unittest.main()
