from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from services.ml_service_client import ml_service_client
from models import BaseResponseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrainingJobRequest(BaseModel):
    service_conf_id: int = Field(..., description='Service configuration ID')
    dataset_files: List[str] = Field(...,
                                     description='List of dataset file names')
    algorithms: Optional[List[str]] = Field(
        default=None, description='Algorithms to train')
    run_name: Optional[str] = Field(
        default=None, description='Custom run name')


class TrainingJobResponse(BaseResponseModel):
    job_id: str


class JobResultRequest(BaseModel):
    job_id: str = Field(..., description='Job ID to retrieve results')
    timeout: int = Field(default=60, description='Timeout in seconds')


class MLTrainingRouter:

    def __init__(self):
        self.router = APIRouter(
            prefix='/api/v1/ml/training',
            tags=['ML Training']
        )
        self._register_routes()

    def _register_routes(self):

        @self.router.post('/submit', response_model=TrainingJobResponse)
        async def submit_training_job(request: TrainingJobRequest):
            try:
                job_id = ml_service_client.submit_training_job(
                    service_conf_id=request.service_conf_id,
                    dataset_files=request.dataset_files,
                    algorithms=request.algorithms,
                    run_name=request.run_name
                )

                return TrainingJobResponse(
                    status=200,
                    message='Training job submitted successfully',
                    job_id=job_id
                )

            except Exception as e:
                logger.error(f"Error submitting training job: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post('/result')
        async def get_training_result(request: JobResultRequest):
            try:
                result = ml_service_client.get_job_result(
                    job_id=request.job_id,
                    timeout=request.timeout
                )

                if result is None:
                    raise HTTPException(
                        status_code=404,
                        detail='Job result not found or timeout reached'
                    )

                return result

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error retrieving job result: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post('/retrain')
        async def trigger_retraining(request: TrainingJobRequest):
            try:
                job_id = ml_service_client.trigger_model_retraining(
                    service_conf_id=request.service_conf_id,
                    dataset_files=request.dataset_files
                )

                return TrainingJobResponse(
                    status=200,
                    message='Model retraining triggered successfully',
                    job_id=job_id
                )

            except Exception as e:
                logger.error(f"Error triggering retraining: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

    def get_router(self) -> APIRouter:
        return self.router
