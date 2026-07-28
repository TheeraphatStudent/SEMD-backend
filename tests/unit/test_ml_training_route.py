"""Domain 10: MLTrainingRouter was completely unregistered (not exported,
not include_router'd) and, if it ever had been wired up as originally
written, would have been reachable with zero authentication on any of its
3 endpoints. Now registered at /ml/training/* and gated to ADMIN/SUPER_ADMIN
via the new AuthGuard.require_admin dependency.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from models.db import User
from guard.auth_guard import AuthGuard
from libs.types.enums import RoleType
from main import app


def _member():
    return User(user_id=1, username='m', email='m@example.com', full_name='M', role=RoleType.MEMBER.value)


def _admin():
    return User(user_id=2, username='a', email='a@example.com', full_name='A', role=RoleType.ADMIN.value)


class MLTrainingRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_registered_and_reachable(self):
        response = self.client.post('/ml/training/submit', json={})
        # 401, not 404 -- proves the route is registered (auth runs before
        # body validation would 422).
        self.assertNotEqual(response.status_code, 404)

    def test_submit_requires_auth(self):
        response = self.client.post(
            '/ml/training/submit',
            json={'service_conf_id': 1, 'dataset_files': ['a.csv']},
        )
        self.assertEqual(response.status_code, 401)

    def test_submit_rejects_non_admin(self):
        app.dependency_overrides[AuthGuard.get_current_user] = _member
        try:
            response = self.client.post(
                '/ml/training/submit',
                json={'service_conf_id': 1, 'dataset_files': ['a.csv']},
            )
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 403)

    def test_submit_allows_admin(self):
        app.dependency_overrides[AuthGuard.get_current_user] = _admin
        try:
            with patch(
                'routers.ml.ml_training_route.ml_service_client.submit_training_job',
                return_value='job-123',
            ):
                response = self.client.post(
                    '/ml/training/submit',
                    json={'service_conf_id': 1, 'dataset_files': ['a.csv']},
                )
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['job_id'], 'job-123')

    def test_retrain_rejects_non_admin(self):
        app.dependency_overrides[AuthGuard.get_current_user] = _member
        try:
            response = self.client.post(
                '/ml/training/retrain',
                json={'service_conf_id': 1, 'dataset_files': ['a.csv']},
            )
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 403)


if __name__ == '__main__':
    unittest.main()
