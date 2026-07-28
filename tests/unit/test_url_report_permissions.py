"""Domain 2 (Users/Roles/Permissions) object-level authorization fix.

Before this change, UrlReportService.update_report performed no ownership or
role check at all: any authenticated MEMBER could edit -- including silently
flipping the review `status` of -- any other user's report by ID. This is a
broken-object-level-authorization (IDOR) bug, not a hypothetical. These tests
pin the fix: non-owner/non-admin members are rejected with 403, owners can
edit their own report but cannot self-approve a status change, and admins can
do both.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from core.exceptions import PermissionDeniedError
from libs.types.enums import FlagType, ReportStatusType, RoleType
from services.url_report_service import UrlReportService


def _fake_user(user_id: int, role: str = RoleType.MEMBER.value):
    return SimpleNamespace(user_id=user_id, role=role)


def _fake_report(report_id: int, owner_id: int, status: str = ReportStatusType.PENDING.value):
    report = SimpleNamespace(
        url_report_id=report_id,
        user_id=owner_id,
        url='https://example.com',
        categories=FlagType.BENIGN.value,
        status=status,
        remark=None,
    )
    return report


def _fake_db(report):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = report
    return db


class UpdateReportRequest(SimpleNamespace):
    url = None
    categories = None
    status = None
    remark = None


class UrlReportPermissionTests(unittest.TestCase):
    def test_non_owner_non_admin_cannot_update(self):
        report = _fake_report(report_id=1, owner_id=100)
        db = _fake_db(report)
        stranger = _fake_user(user_id=999, role=RoleType.MEMBER.value)
        request = UpdateReportRequest(remark='trying to edit someone else\'s report')

        with self.assertRaises(PermissionDeniedError):
            UrlReportService.update_report(stranger, 1, request, db)

    def test_owner_can_update_non_status_fields(self):
        report = _fake_report(report_id=1, owner_id=100)
        db = _fake_db(report)
        owner = _fake_user(user_id=100, role=RoleType.MEMBER.value)
        request = UpdateReportRequest(remark='updated remark')

        updated = UrlReportService.update_report(owner, 1, request, db)
        self.assertEqual(updated.remark, 'updated remark')

    def test_owner_cannot_change_status(self):
        report = _fake_report(report_id=1, owner_id=100, status=ReportStatusType.PENDING.value)
        db = _fake_db(report)
        owner = _fake_user(user_id=100, role=RoleType.MEMBER.value)
        request = UpdateReportRequest(status=ReportStatusType.ACCEPTED)

        with self.assertRaises(PermissionDeniedError):
            UrlReportService.update_report(owner, 1, request, db)

    def test_admin_can_change_any_report_status(self):
        report = _fake_report(report_id=1, owner_id=100, status=ReportStatusType.PENDING.value)
        db = _fake_db(report)
        admin = _fake_user(user_id=999, role=RoleType.ADMIN.value)
        request = UpdateReportRequest(status=ReportStatusType.ACCEPTED)

        updated = UrlReportService.update_report(admin, 1, request, db)
        self.assertEqual(updated.status, ReportStatusType.ACCEPTED.value)


if __name__ == '__main__':
    unittest.main()
