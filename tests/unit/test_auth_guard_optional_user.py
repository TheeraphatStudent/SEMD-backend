"""Coverage for the optional-auth dependency added so the browser extension
can call `/prediction/predict` without a session.

`guard/auth_guard.py::_get_current_user_optional` (exposed as
`AuthGuard.get_current_user_optional`) is the only auth dependency in this
codebase that is *supposed* to swallow authentication failures and degrade to
`None` instead of raising 401. That makes it the one place where an
over-broad `except` or a missing branch turns a hard 401 into a silent
anonymous session -- so every degrade-to-None path is pinned here explicitly.

Tokens are minted with the real `jose.jwt` + the real settings secret rather
than by mocking `AuthService.verify_token`, so the expired/wrong-type cases
exercise the actual verification code path end to end. Only the DB session is
faked.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from jose import jwt

from config.settings import settings
from guard.auth_guard import AuthGuard, _get_current_user_optional

USER_ID = 42


def _token(sub=str(USER_ID), token_type='access', expires_in_minutes=15, **extra):
    payload = {
        'sub': sub,
        'email': 'someone@example.com',
        'role': 'MEMBER',
        'type': token_type,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes),
        **extra,
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm=settings.auth_algorithm)


def _db(user=None):
    """Session stub whose `.query(...).filter(...).first()` yields `user`."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    return db


class GetCurrentUserOptionalTests(unittest.TestCase):

    def test_exposed_on_authguard_as_the_same_function_object(self):
        """FastAPI's dependency_overrides / dependency cache key on identity;
        the class attribute must be the very function the tests exercise."""
        self.assertIs(AuthGuard.get_current_user_optional, _get_current_user_optional)

    def test_missing_authorization_header_returns_none(self):
        db = _db()
        self.assertIsNone(_get_current_user_optional(authorization=None, db=db))
        db.query.assert_not_called()

    def test_empty_authorization_header_returns_none(self):
        self.assertIsNone(_get_current_user_optional(authorization='', db=_db()))

    def test_malformed_header_without_bearer_scheme_returns_none(self):
        for bad in ('token-with-no-scheme', 'Basic dXNlcjpwYXNz', 'Bearer', 'Bearer a b'):
            with self.subTest(authorization=bad):
                db = _db()
                self.assertIsNone(_get_current_user_optional(authorization=bad, db=db))
                db.query.assert_not_called()

    def test_bearer_scheme_is_case_insensitive(self):
        db = _db(user=SimpleNamespace(user_id=USER_ID))
        result = _get_current_user_optional(authorization=f'bearer {_token()}', db=db)
        self.assertIsNotNone(result)

    def test_expired_token_returns_none_instead_of_raising(self):
        """AuthService.verify_token raises HTTPException(401) here -- this
        dependency must catch it, not propagate it."""
        expired = _token(expires_in_minutes=-5)
        self.assertIsNone(_get_current_user_optional(authorization=f'Bearer {expired}', db=_db()))

    def test_garbage_token_returns_none_instead_of_raising(self):
        self.assertIsNone(
            _get_current_user_optional(authorization='Bearer not.a.jwt', db=_db())
        )

    def test_token_signed_with_wrong_secret_returns_none(self):
        forged = jwt.encode(
            {'sub': str(USER_ID), 'type': 'access',
             'exp': datetime.now(timezone.utc) + timedelta(minutes=15)},
            'this-is-not-the-server-secret',
            algorithm=settings.auth_algorithm,
        )
        self.assertIsNone(_get_current_user_optional(authorization=f'Bearer {forged}', db=_db()))

    def test_refresh_token_is_not_accepted_as_an_access_token(self):
        refresh = _token(token_type='refresh')
        self.assertIsNone(_get_current_user_optional(authorization=f'Bearer {refresh}', db=_db()))

    def test_token_without_sub_claim_returns_none(self):
        """int(None) raises TypeError -- must degrade, not 500."""
        no_sub = jwt.encode(
            {'type': 'access', 'exp': datetime.now(timezone.utc) + timedelta(minutes=15)},
            settings.auth_secret_key,
            algorithm=settings.auth_algorithm,
        )
        self.assertIsNone(_get_current_user_optional(authorization=f'Bearer {no_sub}', db=_db()))

    def test_token_with_non_numeric_sub_returns_none(self):
        """int('abc') raises ValueError -- must degrade, not 500."""
        bad_sub = _token(sub='not-an-int')
        self.assertIsNone(_get_current_user_optional(authorization=f'Bearer {bad_sub}', db=_db()))

    def test_valid_token_for_nonexistent_user_returns_none(self):
        """Token verifies, but the user row is gone (deleted account)."""
        self.assertIsNone(
            _get_current_user_optional(authorization=f'Bearer {_token()}', db=_db(user=None))
        )

    def test_valid_token_for_real_user_returns_that_user(self):
        real_user = SimpleNamespace(user_id=USER_ID, username='someone', role='MEMBER')
        result = _get_current_user_optional(authorization=f'Bearer {_token()}', db=_db(real_user))
        self.assertIs(result, real_user)
        self.assertEqual(result.user_id, USER_ID)

    def test_database_errors_are_not_swallowed(self):
        """The docstring narrows 'never raises' to authentication failures --
        a DB failure must still surface rather than silently going anonymous."""
        db = MagicMock()
        db.query.side_effect = RuntimeError('connection pool exhausted')
        with self.assertRaises(RuntimeError):
            _get_current_user_optional(authorization=f'Bearer {_token()}', db=db)


if __name__ == '__main__':
    unittest.main()
