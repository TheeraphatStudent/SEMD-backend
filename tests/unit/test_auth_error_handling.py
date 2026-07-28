"""Characterizes the auth-domain error-handling fix (Phase 3 sample).

Before this change, every one of these router methods wrapped its call in
`except Exception as e: raise HTTPException(500, detail=str(e))` with NO
preceding `except HTTPException: raise` guard -- since HTTPException is itself
an Exception subclass, this silently caught the correctly-typed 401/400/403/404
HTTPExceptions raised by control/auth_control.py and services/auth_service.py
and re-wrapped them as a generic 500 with `detail=str(original_exception)`
(e.g. "401: Invalid username or password"). These tests pin the *fixed*
behavior: typed HTTPExceptions now propagate with their real status code and
detail via the global handler (core/error_handlers.py), and genuinely
unexpected exceptions return a generic message instead of leaking internals.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app


class AuthErrorHandlingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_login_invalid_credentials_returns_401_with_preserved_detail(self):
        """Regression test for the mangled-to-500 bug: this used to come back
        as 500 with detail '401: Invalid username or password'."""
        with patch(
            'control.auth_control.AuthControl.login',
            side_effect=HTTPException(status_code=401, detail='Invalid username or password'),
        ):
            response = self.client.post(
                '/auth/login', json={'username': 'nobody', 'password': 'wrong'}
            )
        self.assertEqual(response.status_code, 401)
        body = response.json()
        self.assertEqual(body['detail'], 'Invalid username or password')
        self.assertEqual(body['code'], 'HTTP_401')

    def test_register_username_conflict_returns_400_with_preserved_detail(self):
        with patch(
            'control.auth_control.AuthControl.register',
            side_effect=HTTPException(status_code=400, detail='Username already exists'),
        ):
            response = self.client.post(
                '/auth/register',
                json={
                    'username': 'taken', 'email': 'taken@example.com',
                    'full_name': 'Taken User', 'password': 'Password123!',
                },
            )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], 'Username already exists')

    def test_unexpected_error_in_login_returns_generic_500_no_leak(self):
        secret_looking_error = "connection to postgresql://svc_user:hunter2@10.0.0.5/semd failed"
        with patch(
            'control.auth_control.AuthControl.login',
            side_effect=RuntimeError(secret_looking_error),
        ):
            response = self.client.post(
                '/auth/login', json={'username': 'anyone', 'password': 'whatever'}
            )
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertNotIn('hunter2', body['detail'])
        self.assertNotIn('postgresql://', body['detail'])
        self.assertEqual(body['code'], 'INTERNAL_ERROR')

    def test_successful_login_shape_unchanged(self):
        fake_token_pair = {
            'access_token': 'a.b.c', 'refresh_token': 'd.e.f', 'token_type': 'bearer'
        }
        with patch('control.auth_control.AuthControl.login', return_value=fake_token_pair):
            response = self.client.post(
                '/auth/login', json={'username': 'someone', 'password': 'correct-horse'}
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        for key, value in fake_token_pair.items():
            self.assertEqual(body[key], value)


if __name__ == '__main__':
    unittest.main()
