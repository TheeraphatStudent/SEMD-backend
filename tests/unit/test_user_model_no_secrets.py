"""Regression test for a severe finding surfaced during Domain 4 work:
UserModel (returned by GET /auth/me, GET /auth/users, GET /auth/users/{id})
used to include password_hash, gg_acc_token/gg_re_token, gh_acc_token/
gh_re_token, twofa_secret, and ex_acc_token verbatim -- meaning every OAuth
refresh token, the TOTP seed, the password hash, and the live extension
token were returned over the API to the profile owner, and to any ADMIN
viewing any other user via the admin user-list/detail endpoints.
"""

from __future__ import annotations

import unittest
from datetime import datetime

from models.auth.user_model import UserModel

_SECRET_FIELDS = (
    'password_hash', 'gg_acc_token', 'gg_re_token',
    'gh_acc_token', 'gh_re_token', 'twofa_secret', 'ex_acc_token',
)


class UserModelSecretExposureTests(unittest.TestCase):
    def test_secret_fields_are_not_part_of_the_schema(self):
        field_names = set(UserModel.model_fields.keys())
        for secret_field in _SECRET_FIELDS:
            self.assertNotIn(secret_field, field_names, f'{secret_field} must not be a UserModel field')

    def test_non_secret_connected_account_fields_still_present(self):
        field_names = set(UserModel.model_fields.keys())
        for keep_field in ('gg_id', 'gh_id', 'is_2fa_enabled', 'ex_acc_token_exp'):
            self.assertIn(keep_field, field_names)

    def test_model_validate_from_orm_like_object_does_not_error(self):
        class FakeOrmUser:
            user_id = 1
            username = 'u'
            email = 'u@example.com'
            full_name = 'U'
            birthday = None
            role = 'MEMBER'
            gg_id = None
            gh_id = None
            is_2fa_enabled = False
            ex_acc_token_exp = None
            profile_img_uri = None
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()

        model = UserModel.model_validate(FakeOrmUser())
        dumped = model.model_dump()
        for secret_field in _SECRET_FIELDS:
            self.assertNotIn(secret_field, dumped)


if __name__ == '__main__':
    unittest.main()
