"""Domain 10: the most severe finding of this audit. Every ML model-registry
mutation endpoint (register, update, change stage, promote-to-production,
activate, deactivate, delete) previously required only `get_current_user` --
any authenticated MEMBER could register a model pointing at an arbitrary
model_uri/scaler_uri and then promote or activate it, redirecting every
user's prediction traffic to a model they control. Fixed: all 7 mutation
endpoints gated to AuthGuard.require_admin. Read-only listing and prediction
endpoints intentionally remain any-authenticated-user.
"""

from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from models.db import User
from guard.auth_guard import AuthGuard
from libs.types.enums import RoleType
from main import app


def _member():
    return User(user_id=1, username='m', email='m@example.com', full_name='M', role=RoleType.MEMBER.value)


_MUTATING_REQUESTS = [
    ('POST', '/ml/models', {'name': 'x', 'algorithm': 'svm', 'mlflow_run_id': 'r', 'model_uri': 'u', 'scaler_uri': 'u', 'label_uri': 'u', 'selecter_uri': 'u'}),
    ('PUT', '/ml/models/1', {}),
    ('PATCH', '/ml/models/1/stage', {'stage': 'PRODUCTION'}),
    ('POST', '/ml/models/1/promote', None),
    ('POST', '/ml/models/1/activate', None),
    ('POST', '/ml/models/1/deactivate', None),
    ('DELETE', '/ml/models/1', None),
]


class MlModelRegistryPermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_all_mutating_endpoints_reject_non_admin(self):
        app.dependency_overrides[AuthGuard.get_current_user] = _member
        try:
            for method, path, body in _MUTATING_REQUESTS:
                with self.subTest(method=method, path=path):
                    response = self.client.request(method, path, json=body)
                    self.assertEqual(
                        response.status_code, 403,
                        f'{method} {path} should require admin, got {response.status_code}: {response.text}'
                    )
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)

    def test_all_mutating_endpoints_require_auth(self):
        for method, path, body in _MUTATING_REQUESTS:
            with self.subTest(method=method, path=path):
                response = self.client.request(method, path, json=body)
                self.assertEqual(response.status_code, 401)

    def test_get_service_no_longer_crashes(self):
        app.dependency_overrides[AuthGuard.get_current_user] = _member
        try:
            response = self.client.get('/ml/service')
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 501)


if __name__ == '__main__':
    unittest.main()
