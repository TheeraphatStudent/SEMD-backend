from sqlalchemy.orm import Session
from typing import List

from database import User, UrlReport, UrlReported
from models.url_report_request import UrlReportCreateRequest, UrlReportUpdateRequest
from models.url_report_model import UrlReportModel
from models.url_reported_model import UrlReportedModel
from services.url_report_service import UrlReportService


class UrlReportControl:
    
    @classmethod
    def create_report(cls, user: User, request: UrlReportCreateRequest, db: Session) -> UrlReportModel:
        report = UrlReportService.create_report(user, request, db)
        return UrlReportModel.model_validate(report)
    
    @classmethod
    def update_report(cls, user: User, report_id: int, request: UrlReportUpdateRequest, db: Session) -> UrlReportModel:
        report = UrlReportService.update_report(user, report_id, request, db)
        return UrlReportModel.model_validate(report)
    
    @classmethod
    def get_report(cls, report_id: int, db: Session) -> UrlReportModel:
        report = UrlReportService.get_report_by_id(report_id, db)
        return UrlReportModel.model_validate(report)
    
    @classmethod
    def get_all_reports(cls, db: Session, skip: int = 0, limit: int = 100) -> List[UrlReportModel]:
        reports = UrlReportService.get_all_reports(db, skip, limit)
        return [UrlReportModel.model_validate(r) for r in reports]
    
    @classmethod
    def get_user_reports(cls, user: User, db: Session, skip: int = 0, limit: int = 100) -> List[UrlReportModel]:
        reports = UrlReportService.get_reports_by_user(user.user_id, db, skip, limit)
        return [UrlReportModel.model_validate(r) for r in reports]
    
    @classmethod
    def get_report_history(cls, report_id: int, db: Session) -> List[UrlReportedModel]:
        history = UrlReportService.get_report_history(report_id, db)
        return [UrlReportedModel.model_validate(h) for h in history]


url_report_control = UrlReportControl()
