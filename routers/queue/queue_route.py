from routers import BaseRoute
from models import BaseResponseModel
from models.queue_model import QueueItemResponse
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Any
from pydantic import Field

from control.queue_control import QueueControl
from guard.auth_guard import AuthGuard, get_db
from database import User
from libs.types.enums import RoleType


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
        current_user: User = Depends(AuthGuard.get_current_user),
        db: Session = Depends(get_db)
    ):
        try:
            queue_data = QueueControl.get_retrain_queue()
            return QueueListResponse(
                status=200,
                message="Retrain queue retrieved successfully",
                data=queue_data
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
