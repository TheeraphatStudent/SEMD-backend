"""Domain 11: GET /queue/url exposes other users' username/user_id/
profile_img_url tied to specific URLs they submitted for prediction
(models/queue_model.py::PredictByInfo). Previously any authenticated
MEMBER could view it; no owner-scoped alternative exists (unlike
/report/me). Gated to admin as an internal ML-pipeline monitoring view.
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


class QueueRoutePermissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_requires_auth(self):
        response = self.client.get('/queue/url')
        self.assertEqual(response.status_code, 401)

    def test_member_forbidden(self):
        app.dependency_overrides[AuthGuard.get_current_user] = _member
        try:
            response = self.client.get('/queue/url')
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 403)

    def test_admin_allowed(self):
        app.dependency_overrides[AuthGuard.get_current_user] = _admin
        try:
            with patch('control.queue_control.QueueControl.get_retrain_queue', return_value={'total': 0, 'items': []}):
                response = self.client.get('/queue/url')
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
