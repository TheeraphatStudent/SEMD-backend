"""Domain 9: the 32 Dashboard/Stat endpoints were unauthenticated `pass`
stubs that returned `None` against a declared response_model -- FastAPI
turns that into a 500 on every single call, and there was no auth check at
all. Fixed: authenticated (401 without a token), and an honest 501
(NotImplementedFeatureError) instead of a response-validation crash.
Spot-checks one endpoint per router (8 routers) rather than all 32 --
the fix is mechanically identical across all of them.
"""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from models.db import User
from guard.auth_guard import AuthGuard
from main import app


def _fake_user():
    return User(user_id=1, username='u', email='u@example.com', full_name='U', role='MEMBER')


_ENDPOINTS = [
    '/dashboard/system-stat',
    '/stat/report',
    '/stat/prediction',
    '/stat/user',
    '/stat/api-key',
    '/stat/third-party',
    '/stat/url-flag',
]


class DashboardStubEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_all_spot_checked_endpoints_require_auth(self):
        for path in _ENDPOINTS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 401)

    def test_all_spot_checked_endpoints_return_honest_501_when_authenticated(self):
        app.dependency_overrides[AuthGuard.get_current_user] = _fake_user
        try:
            for path in _ENDPOINTS:
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 501)
                    self.assertEqual(response.json()['code'], 'NOT_IMPLEMENTED')
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)


if __name__ == '__main__':
    unittest.main()
