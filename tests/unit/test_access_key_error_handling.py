"""Domain 3 (API Access Keys) error-handling sweep.

Unlike auth, most of this file's 13 broad-exception sites already had the
`except HTTPException: raise` guard -- so the mangled-to-500 bug was narrower
here (only `get_my_keys` lacked it, and nothing in its call chain currently
raises HTTPException, so there was no live-bug instance to regress-test).
The one site that mattered structurally was `create_extension_token`, which
does `db.rollback()` before its raise -- that cleanup call is preserved, only
the `str(e)` leak is fixed. These tests pin: (1) the existing correct 403
ownership-check behavior in the usage endpoints still works after removing
the wrapper, (2) create_extension_token still rolls back and no longer leaks
exception text.
"""

from __future__ import annotations

import hashlib
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from models.db import User
from guard.auth_guard import AuthGuard
from main import app


def _fake_user(user_id=1, role='MEMBER'):
    return User(user_id=user_id, username='u', email='u@example.com', full_name='U', role=role)


class AccessKeyErrorHandlingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_usage_ownership_check_403_preserved(self):
        app.dependency_overrides[AuthGuard.get_current_user] = lambda: _fake_user(user_id=1)
        try:
            with patch(
                'control.access_key_control.AccessKeyControl.get_key_usage_monthly',
                side_effect=HTTPException(status_code=403, detail="You don't have permission to view this key's usage"),
            ):
                response = self.client.get('/setting/access-key/5/usage/monthly?year=2026&month=1')
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 403)
        self.assertIn('permission', response.json()['detail'])

    def test_admin_endpoint_rejects_non_admin_with_403(self):
        app.dependency_overrides[AuthGuard.get_current_user] = lambda: _fake_user(user_id=1, role='MEMBER')
        try:
            response = self.client.get('/setting/access-key/admin')
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 403)

    def test_extension_token_rolls_back_and_does_not_leak(self):
        app.dependency_overrides[AuthGuard.get_current_user] = lambda: _fake_user(user_id=1)
        try:
            with patch(
                'sqlalchemy.orm.Session.commit',
                side_effect=RuntimeError('duplicate key value violates unique constraint "users_pkey"'),
            ), patch('sqlalchemy.orm.Session.rollback') as mock_rollback:
                response = self.client.post('/setting/access-key/extension/token')
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertNotIn('users_pkey', body['detail'])
        self.assertNotIn('constraint', body['detail'])
        mock_rollback.assert_called_once()

    def test_extension_token_stored_as_hash_not_plaintext(self):
        """Domain 4 fix: previously stored the raw token in User.ex_acc_token.
        The response still returns the raw token once (that's correct --
        matches the access-key "show once" pattern) but what lands in the DB
        must be the hash, matching AccessKey's storage pattern."""
        user = _fake_user(user_id=1)
        app.dependency_overrides[AuthGuard.get_current_user] = lambda: user
        try:
            with patch('sqlalchemy.orm.Session.commit'), patch('sqlalchemy.orm.Session.refresh'):
                response = self.client.post('/setting/access-key/extension/token')
        finally:
            app.dependency_overrides.pop(AuthGuard.get_current_user, None)
        self.assertEqual(response.status_code, 200)
        raw_token = response.json()['data']['ex_acc_token']
        self.assertEqual(len(raw_token), 6)
        # The mutated `user` object is the same instance the route wrote to.
        self.assertEqual(user.ex_acc_token, hashlib.sha256(raw_token.encode()).hexdigest())
        self.assertNotEqual(user.ex_acc_token, raw_token)


if __name__ == '__main__':
    unittest.main()
