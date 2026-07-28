from __future__ import annotations

import unittest

from fastapi.testclient import TestClient


class ApplicationBootTests(unittest.TestCase):
    """Guards against import-time regressions (module-level singletons, router
    registration order, the openapi.yaml write) since this app builds `app` at
    import time rather than behind an explicit factory."""

    @classmethod
    def setUpClass(cls):
        from main import app
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_docs_available(self):
        response = self.client.get('/docs')
        self.assertEqual(response.status_code, 200)

    def test_openapi_schema_generates(self):
        response = self.client.get('/openapi.json')
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertGreater(len(schema.get('paths', {})), 50)

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)

    def test_liveness_always_ok(self):
        response = self.client.get('/health/live')
        self.assertEqual(response.status_code, 200)

    def test_readiness_reports_dependency_status(self):
        # Doesn't assert 200 vs 503 -- depends on whether Postgres/Redis are
        # reachable in the environment running the test. Asserts the shape.
        response = self.client.get('/health/ready')
        self.assertIn(response.status_code, (200, 503))
        body = response.json()
        self.assertIn('checks', body)
        self.assertIn('database', body['checks'])
        self.assertIn('redis', body['checks'])

    def test_request_id_header_present(self):
        response = self.client.get('/')
        self.assertIn('x-request-id', response.headers)


if __name__ == '__main__':
    unittest.main()
