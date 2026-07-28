
from fastapi import Depends, Query
from sqlalchemy.orm import Session

from control.url_report_control import UrlReportControl
from models.db import User
from guard.auth_guard import AuthGuard, get_db
from models import ReportListResponse, ReportResponse
from models.report.url_report_request import UrlReportCreateRequest, UrlReportUpdateRequest
from routers import BaseRoute


class ReportRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/report",
            tags=["report"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}, 422: {"description": "Validation error"}}
        )

        self.router.get(
            "",
            response_model=ReportListResponse,
            summary="Get All Reports",
            description="Get all URL reports. Requires authentication."
        )(self.get_report_data)
        
        self.router.get(
            "/me",
            response_model=ReportListResponse,
            summary="Get My Reports",
            description="Get URL reports created by the current user."
        )(self.get_my_reports)
        
        self.router.get(
            "/{report_id}",
            response_model=ReportResponse,
            summary="Get Report by ID",
            description="Get a specific URL report by its ID."
        )(self.get_report_by_id)
        
        self.router.get(
            "/{report_id}/history",
            response_model=ReportListResponse,
            summary="Get Report History",
            description="Get the action history of a specific URL report."
        )(self.get_report_history)
        
        self.router.post(
            "",
            response_model=ReportResponse,
            summary="Create Report",
            description="Create a new URL report. Requires authentication."
        )(self.create_report)
        
        self.router.put(
            "/{report_id}",
            response_model=ReportResponse,
            summary="Update Report",
            description="Update an existing URL report. Requires authentication."
        )(self.update_report)

    async def create_report(
        self,
        request: UrlReportCreateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        report = UrlReportControl.create_report(current_user, request, db)
        return ReportResponse(status=201, message="Report created successfully", data=report.model_dump())

    async def update_report(
        self,
        report_id: int,
        request: UrlReportUpdateRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        report = UrlReportControl.update_report(current_user, report_id, request, db)
        return ReportResponse(status=200, message="Report updated successfully", data=report.model_dump())

    async def get_report_data(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        reports = UrlReportControl.get_all_reports(db, skip, limit)
        return ReportListResponse(status=200, message="Reports retrieved successfully", data=[r.model_dump() for r in reports])

    async def get_my_reports(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        reports = UrlReportControl.get_user_reports(current_user, db, skip, limit)
        return ReportListResponse(status=200, message="Reports retrieved successfully", data=[r.model_dump() for r in reports])

    async def get_report_by_id(
        self,
        report_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        report = UrlReportControl.get_report(report_id, db)
        return ReportResponse(status=200, message="Report retrieved successfully", data=report.model_dump())

    async def get_report_history(
        self,
        report_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        history = UrlReportControl.get_report_history(report_id, db)
        return ReportListResponse(status=200, message="Report history retrieved successfully", data=[h.model_dump() for h in history])
