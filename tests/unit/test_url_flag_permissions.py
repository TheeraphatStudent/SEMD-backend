"""Domain 8 (URL Flags): critical finding fix.

Before this change, ANY authenticated MEMBER could create, edit, or promote
a URL flag to `access_level=GLOBAL`. Global flags are applied to EVERY
user's prediction result (services/url_flag_service.py::check_url_flag /
check_url_flag_async: `access_level == GLOBAL OR user_id == caller`) --
meaning any account could unilaterally whitelist a malicious URL or
blacklist a legitimate one for the entire user base. Also fixed: an admin
previously could not delete another user's rogue GLOBAL flag (no admin
override existed at all in this domain before this pass).
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from core.exceptions import PermissionDeniedError
from libs.types.enums import ACLType, FlagType, RoleType
from services.url_flag_service import UrlFlagService


def _fake_user(user_id: int, role: str = RoleType.MEMBER.value):
    return SimpleNamespace(user_id=user_id, role=role)


def _fake_flag(flag_id: int, owner_id: int, access_level: str = ACLType.PRIVATE.value):
    return SimpleNamespace(
        url_flag_id=flag_id,
        user_id=owner_id,
        url='https://example.com',
        type=FlagType.BENIGN.value,
        access_level=access_level,
    )


def _fake_db(flag=None):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = flag
    return db


class CreateFlagRequest(SimpleNamespace):
    url = 'https://example.com'
    type = FlagType.BENIGN
    access_level = ACLType.PRIVATE


class UpdateFlagRequest(SimpleNamespace):
    url = None
    type = None
    access_level = None


class UrlFlagGlobalPermissionTests(unittest.TestCase):
    def test_member_cannot_create_global_flag(self):
        member = _fake_user(user_id=1)
        request = CreateFlagRequest(access_level=ACLType.GLOBAL)
        with self.assertRaises(PermissionDeniedError):
            UrlFlagService.create_flag(member, request, _fake_db())

    def test_member_can_create_private_flag(self):
        member = _fake_user(user_id=1)
        request = CreateFlagRequest(access_level=ACLType.PRIVATE)
        db = _fake_db()
        flag = UrlFlagService.create_flag(member, request, db)
        self.assertEqual(flag.access_level, ACLType.PRIVATE.value)

    def test_admin_can_create_global_flag(self):
        admin = _fake_user(user_id=1, role=RoleType.ADMIN.value)
        request = CreateFlagRequest(access_level=ACLType.GLOBAL)
        db = _fake_db()
        flag = UrlFlagService.create_flag(admin, request, db)
        self.assertEqual(flag.access_level, ACLType.GLOBAL.value)

    def test_member_cannot_promote_own_flag_to_global(self):
        owner = _fake_user(user_id=1)
        flag = _fake_flag(flag_id=1, owner_id=1, access_level=ACLType.PRIVATE.value)
        db = _fake_db(flag)
        request = UpdateFlagRequest(access_level=ACLType.GLOBAL)
        with self.assertRaises(PermissionDeniedError):
            UrlFlagService.update_flag(owner, 1, request, db)

    def test_member_cannot_edit_existing_global_flag_even_if_owner(self):
        # Edge case: a global flag somehow owned by a non-admin (e.g. role
        # was demoted after creation) still requires admin to edit.
        owner = _fake_user(user_id=1, role=RoleType.MEMBER.value)
        flag = _fake_flag(flag_id=1, owner_id=1, access_level=ACLType.GLOBAL.value)
        db = _fake_db(flag)
        request = UpdateFlagRequest(url='https://changed.example.com')
        with self.assertRaises(PermissionDeniedError):
            UrlFlagService.update_flag(owner, 1, request, db)

    def test_admin_can_delete_another_users_global_flag(self):
        admin = _fake_user(user_id=999, role=RoleType.ADMIN.value)
        flag = _fake_flag(flag_id=1, owner_id=1, access_level=ACLType.GLOBAL.value)
        db = _fake_db(flag)
        result = UrlFlagService.delete_flag(admin, 1, db)
        self.assertTrue(result)

    def test_stranger_still_cannot_delete_others_private_flag(self):
        stranger = _fake_user(user_id=999, role=RoleType.MEMBER.value)
        flag = _fake_flag(flag_id=1, owner_id=1, access_level=ACLType.PRIVATE.value)
        db = _fake_db(flag)
        with self.assertRaises(PermissionDeniedError):
            UrlFlagService.delete_flag(stranger, 1, db)


if __name__ == '__main__':
    unittest.main()
