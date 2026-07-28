
from fastapi import Depends
from pydantic import Field
from sqlalchemy.orm import Session

from control.queue_control import QueueControl
from models.db import User
from guard.auth_guard import AuthGuard, get_db
from models import BaseResponseModel
from routers import BaseRoute


class QueueListResponse(BaseResponseModel):
    data: dict = Field(title="data", description="Queue data with total and items")


class QueueRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/queue",
            tags=["queue"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}}
        )

        self.router.get(
            "/url",
            response_model=QueueListResponse,
            summary="Get Retrain Queue",
            description="Get all URLs waiting for retraining. Shows prediction info with user details."
        )(self.get_retrain_queue)

    async def get_retrain_queue(
        self,
        # Was any-authenticated-user. This endpoint exposes OTHER users'
        # username/user_id/profile_img_url tied to specific URLs they
        # predicted (see models/queue_model.py::PredictByInfo) -- an
        # internal ML-pipeline monitoring view, not a user-facing feature
        # (no owner-scoped "my queue items" variant exists, unlike
        # /report/me). Gated to admin: see
        # docs/backend/features/dataset-retraining/README.md.
        current_user: User = Depends(AuthGuard.require_admin),
        db: Session = Depends(get_db)
    ):
        queue_data = QueueControl.get_retrain_queue()
        return QueueListResponse(
            status=200,
            message="Retrain queue retrieved successfully",
            data=queue_data
        )
