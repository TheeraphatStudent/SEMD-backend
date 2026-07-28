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
        # Present-and-None (rather than absent) on purpose: SimpleNamespace
        # accepts any attribute write silently, so without seeding these the
        # reviewed_by/reviewed_at assertions below could never fail and the
        # tests would pass even if the feature were reverted.
        reviewed_by=None,
        reviewed_at=None,
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
        # Human-over-AI review attribution is recorded directly on the row.
        self.assertEqual(updated.reviewed_by, admin.user_id)
        self.assertIsNotNone(updated.reviewed_at)

    def test_status_change_stamps_a_timezone_aware_reviewed_at(self):
        """reviewed_at lands in a TIMESTAMPTZ column -- a naive datetime would
        be silently reinterpreted in the server's timezone."""
        report = _fake_report(report_id=1, owner_id=100, status=ReportStatusType.PENDING.value)
        db = _fake_db(report)
        admin = _fake_user(user_id=999, role=RoleType.ADMIN.value)
        request = UpdateReportRequest(status=ReportStatusType.ACCEPTED)

        updated = UrlReportService.update_report(admin, 1, request, db)
        self.assertIsNotNone(updated.reviewed_at.tzinfo)

    def test_update_without_status_change_leaves_review_fields_unset(self):
        """Negative case for reviewed_by/reviewed_at: editing only `remark`
        must not stamp a review that never happened."""
        report = _fake_report(report_id=1, owner_id=100)
        db = _fake_db(report)
        owner = _fake_user(user_id=100, role=RoleType.MEMBER.value)
        request = UpdateReportRequest(remark='fixing a typo in my own report')

        updated = UrlReportService.update_report(owner, 1, request, db)
        self.assertEqual(updated.remark, 'fixing a typo in my own report')
        self.assertIsNone(updated.reviewed_by)
        self.assertIsNone(updated.reviewed_at)

    def test_admin_resubmitting_the_same_status_does_not_stamp_a_review(self):
        """`status` present in the request but identical to the current value
        is not a status *change* -- it must not count as a review."""
        report = _fake_report(report_id=1, owner_id=100, status=ReportStatusType.ACCEPTED.value)
        db = _fake_db(report)
        admin = _fake_user(user_id=999, role=RoleType.ADMIN.value)
        request = UpdateReportRequest(status=ReportStatusType.ACCEPTED)

        updated = UrlReportService.update_report(admin, 1, request, db)
        self.assertIsNone(updated.reviewed_by)
        self.assertIsNone(updated.reviewed_at)


if __name__ == '__main__':
    unittest.main()
