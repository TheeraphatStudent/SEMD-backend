from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.error_handlers import register_error_handlers
from core.exceptions import NotFoundError
from core.middleware import RequestContextMiddleware


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    register_error_handlers(app)

    @app.get('/boom-app-error')
    async def boom_app_error():
        raise NotFoundError('widget 42 not found')

    @app.get('/boom-http-exception')
    async def boom_http_exception():
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail='nope')

    @app.get('/boom-unexpected')
    async def boom_unexpected():
        raise ValueError('super secret internal detail: password=hunter2')

    @app.get('/validated')
    async def validated(count: int):
        return {'count': count}

    return app


class ErrorHandlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(_build_test_app(), raise_server_exceptions=False)

    def test_app_error_shape(self):
        response = self.client.get('/boom-app-error')
        self.assertEqual(response.status_code, 404)
        body = response.json()
        self.assertEqual(body['code'], 'NOT_FOUND')
        self.assertEqual(body['status'], 404)
        self.assertEqual(body['detail'], 'widget 42 not found')
        self.assertIn('request_id', body)
        self.assertIn('type', body)
        self.assertIn('instance', body)

    def test_http_exception_shape_preserves_detail(self):
        response = self.client.get('/boom-http-exception')
        self.assertEqual(response.status_code, 403)
        body = response.json()
        # `detail` preserved so a client only reading `detail` (today's shape)
        # keeps working -- this is what makes the rollout additive, not breaking.
        self.assertEqual(body['detail'], 'nope')
        self.assertEqual(body['code'], 'HTTP_403')

    def test_unexpected_exception_does_not_leak_internal_detail(self):
        response = self.client.get('/boom-unexpected')
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertNotIn('hunter2', body['detail'])
        self.assertNotIn('password', body['detail'].lower())
        self.assertEqual(body['code'], 'INTERNAL_ERROR')

    def test_validation_error_shape(self):
        response = self.client.get('/validated', params={'count': 'not-an-int'})
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body['code'], 'VALIDATION_ERROR')
        self.assertTrue(body['errors'])


if __name__ == '__main__':
    unittest.main()
