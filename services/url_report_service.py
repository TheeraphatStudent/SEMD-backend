from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.exceptions import PermissionDeniedError
from models.db import UrlReport, UrlReported, User
from libs.types.enums import RoleType
from models.report.url_report_request import UrlReportCreateRequest, UrlReportUpdateRequest

_ADMIN_ROLES = (RoleType.ADMIN.value, RoleType.SUPER_ADMIN.value)


class UrlReportService:

    @classmethod
    def create_report(cls, user: User, request: UrlReportCreateRequest, db: Session) -> UrlReport:
        new_report = UrlReport(
            user_id=user.user_id,
            url=request.url,
            categories=request.categories.value,
            status=request.status.value,
            remark=request.remark
        )

        db.add(new_report)
        db.commit()
        db.refresh(new_report)

        cls._log_action(
            db=db,
            url_report_id=new_report.url_report_id,
            user_id=user.user_id,
            action='CREATE',
            old_status=None,
            new_status=request.status.value,
            remark=f"Report created for URL: {request.url}"
        )

        return new_report

    @classmethod
    def update_report(cls, user: User, report_id: int, request: UrlReportUpdateRequest, db: Session) -> UrlReport:
        report = db.query(UrlReport).filter(
            UrlReport.url_report_id == report_id).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with id {report_id} not found"
            )

        is_owner = report.user_id == user.user_id
        is_admin = user.role in _ADMIN_ROLES

        # Object-level authorization: previously any authenticated user could
        # edit -- including status-transition -- any other user's report,
        # bypassing the review workflow entirely. See
        # docs/backend/features/users-roles-permissions/README.md.
        if not is_owner and not is_admin:
            raise PermissionDeniedError('You do not have permission to update this report')

        if request.status is not None and request.status.value != report.status and not is_admin:
            raise PermissionDeniedError('Only an admin can change a report\'s review status')

        old_status = report.status

        if request.url is not None:
            report.url = request.url
        if request.categories is not None:
            report.categories = request.categories.value
        if request.status is not None:
            report.status = request.status.value
        if request.remark is not None:
            report.remark = request.remark

        report.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(report)

        new_status = report.status
        action = 'UPDATE'
        if old_status != new_status:
            action = 'STATUS_CHANGE'

        cls._log_action(
            db=db,
            url_report_id=report.url_report_id,
            user_id=user.user_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            remark=request.remark or f"Report updated by user {user.user_id}"
        )

        return report

    @classmethod
    def get_report_by_id(cls, report_id: int, db: Session) -> UrlReport:
        report = db.query(UrlReport).filter(
            UrlReport.url_report_id == report_id).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with id {report_id} not found"
            )

        return report

    @classmethod
    def get_all_reports(cls, db: Session, skip: int = 0, limit: int = 100) -> List[UrlReport]:
        return db.query(UrlReport).offset(skip).limit(limit).all()

    @classmethod
    def get_reports_by_user(cls, user_id: int, db: Session, skip: int = 0, limit: int = 100) -> List[UrlReport]:
        return db.query(UrlReport).filter(UrlReport.user_id == user_id).offset(skip).limit(limit).all()

    @classmethod
    def get_report_history(cls, report_id: int, db: Session) -> List[UrlReported]:
        return db.query(UrlReported).filter(UrlReported.url_report_id == report_id).order_by(UrlReported.created_at.desc()).all()

    @classmethod
    def _log_action(
        cls,
        db: Session,
        url_report_id: int,
        user_id: int,
        action: str,
        old_status: Optional[str],
        new_status: Optional[str],
        remark: Optional[str] = None
    ) -> UrlReported:
        log_entry = UrlReported(
            url_report_id=url_report_id,
            user_id=user_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            remark=remark
        )

        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        return log_entry


url_report_service = UrlReportService()
