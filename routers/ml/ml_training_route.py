import logging
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from core.exceptions import NotFoundError
from models.db import User
from guard.auth_guard import AuthGuard
from models import BaseResponseModel
from services.ml_service_client import ml_service_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainingJobRequest(BaseModel):
    service_conf_id: int = Field(..., description="Service configuration ID")
    dataset_files: List[str] = Field(..., description="List of dataset file names")
    algorithms: Optional[List[str]] = Field(default=None, description="Algorithms to train")
    run_name: Optional[str] = Field(default=None, description="Custom run name")


class TrainingJobResponse(BaseResponseModel):
    job_id: str


class JobResultRequest(BaseModel):
    job_id: str = Field(..., description="Job ID to retrieve results")
    timeout: int = Field(default=60, description="Timeout in seconds")


class MLTrainingRouter:
    """Was completely unregistered dead code until this pass (Domain 10) --
    not exported from routers/ml/__init__.py, never include_router'd in
    application.py, and every endpoint below had zero auth dependency. The
    underlying services.ml_service_client methods it calls are real, working
    implementations (Redis-queue-backed job submission/result polling), so
    this was a half-wired feature rather than genuinely dead code -- wired up
    here rather than deleted. Prefix normalized from the original
    `/api/v1/ml/training` (redundant `/api` -- already the app's root_path --
    plus a `/v1` segment nothing else in this backend uses) to `/ml/training`,
    matching every other router's convention. Training/retraining are
    privileged, resource-intensive operations -- gated to ADMIN/SUPER_ADMIN,
    not just any authenticated user.
    """

    def __init__(self):
        self.router = APIRouter(
            prefix="/ml/training",
            tags=["ML Training"]
        )
        self._register_routes()

    def _register_routes(self):

        @self.router.post("/submit", response_model=TrainingJobResponse)
        async def submit_training_job(
            request: TrainingJobRequest,
            current_user: User = Depends(AuthGuard.require_admin),
        ):
            job_id = ml_service_client.submit_training_job(
                service_conf_id=request.service_conf_id,
                dataset_files=request.dataset_files,
                algorithms=request.algorithms,
                run_name=request.run_name
            )

            return TrainingJobResponse(
                status=200,
                message="Training job submitted successfully",
                job_id=job_id
            )

        @self.router.post("/result")
        async def get_training_result(
            request: JobResultRequest,
            current_user: User = Depends(AuthGuard.require_admin),
        ):
            result = await ml_service_client.get_job_result(
                job_id=request.job_id,
                timeout=request.timeout
            )

            if result is None:
                raise NotFoundError('Job result not found or timeout reached')

            return result

        @self.router.post("/retrain", response_model=TrainingJobResponse)
        async def trigger_retraining(
            request: TrainingJobRequest,
            current_user: User = Depends(AuthGuard.require_admin),
        ):
            job_id = ml_service_client.trigger_model_retraining(
                service_conf_id=request.service_conf_id,
                dataset_files=request.dataset_files
            )

            return TrainingJobResponse(
                status=200,
                message="Model retraining triggered successfully",
                job_id=job_id
            )

    def get_router(self) -> APIRouter:
        return self.router
