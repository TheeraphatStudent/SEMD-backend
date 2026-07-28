from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from control.model_registry_control import ModelRegistryControl
from core.exceptions import NotImplementedFeatureError
from models.db import User
from guard.auth_guard import AuthGuard, get_async_db
from libs.types.enums import ModelStageType
from models import MLServiceResponse
from models.service.model_registry_request import (
    MLBatchPredictRequest,
    MLPredictRequest,
    ModelRegistryCreateRequest,
    ModelRegistryUpdateRequest,
    ModelStageUpdateRequest,
)
from models.service.model_registry_response import (
    MLBatchPredictResponse,
    MLPredictResponse,
    ModelRegistryListResponse,
    ModelRegistryResponse,
)
from routers import BaseRoute
from services.ml_prediction_service import MLPredictionService


class MLRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/ml",
            tags=["ml"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get("/service", response_model=MLServiceResponse)(self.get_service)

        # Model Registry CRUD endpoints
        self.router.post(
            "/models",
            response_model=ModelRegistryResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Register Model",
            description="Register a new ML model in the registry"
        )(self.create_model)

        self.router.get(
            "/models",
            response_model=ModelRegistryListResponse,
            summary="List Models",
            description="List all registered ML models"
        )(self.list_models)

        self.router.get(
            "/models/production",
            response_model=ModelRegistryResponse,
            summary="Get Production Model",
            description="Get the current production model"
        )(self.get_production_model)

        self.router.get(
            "/models/{model_id}",
            response_model=ModelRegistryResponse,
            summary="Get Model",
            description="Get a specific model by ID"
        )(self.get_model)

        self.router.put(
            "/models/{model_id}",
            response_model=ModelRegistryResponse,
            summary="Update Model",
            description="Update a model registry entry"
        )(self.update_model)

        self.router.patch(
            "/models/{model_id}/stage",
            response_model=ModelRegistryResponse,
            summary="Update Model Stage",
            description="Update the stage of a model"
        )(self.update_model_stage)

        self.router.post(
            "/models/{model_id}/promote",
            response_model=ModelRegistryResponse,
            summary="Promote to Production",
            description="Promote a model to production stage"
        )(self.promote_to_production)

        self.router.post(
            "/models/{model_id}/activate",
            response_model=ModelRegistryResponse,
            summary="Activate Model",
            description="Activate a model"
        )(self.activate_model)

        self.router.post(
            "/models/{model_id}/deactivate",
            response_model=ModelRegistryResponse,
            summary="Deactivate Model",
            description="Deactivate a model"
        )(self.deactivate_model)

        self.router.delete(
            "/models/{model_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete Model",
            description="Delete a model from the registry"
        )(self.delete_model)

        # Prediction endpoints
        self.router.post(
            "/predict",
            response_model=MLPredictResponse,
            summary="Predict URL",
            description="Predict if a URL is malicious"
        )(self.predict_url)

        self.router.post(
            "/predict/batch",
            response_model=MLBatchPredictResponse,
            summary="Batch Predict URLs",
            description="Predict multiple URLs"
        )(self.predict_batch)

    async def get_service(self, current_user: User = Depends(AuthGuard.get_current_user)):
        # Was `return None` against a declared response_model=MLServiceResponse
        # -- same response-validation-crash-on-every-call bug fixed for the
        # 32 Dashboard/Stat stubs in Domain 9. Same fix: authenticated,
        # honest 501 instead of a silent 500.
        raise NotImplementedFeatureError('ML service status endpoint is not implemented yet')

    async def create_model(
        self,
        request: ModelRegistryCreateRequest,
        current_user: User = Depends(AuthGuard.require_admin),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        model = await control.create_model(
            name=request.name,
            algorithm=request.algorithm,
            mlflow_run_id=request.mlflow_run_id,
            model_uri=request.model_uri,
            scaler_uri=request.scaler_uri,
            label_uri=request.label_uri,
            selecter_uri=request.selecter_uri,
            mlflow_model_version=request.mlflow_model_version,
            experiment_id=request.experiment_id,
            stage=request.stage,
            accuracy_score=request.accuracy_score,
            recall_score=request.recall_score,
            precision_score=request.precision_score,
            f1_score=request.f1_score,
            description=request.description,
            tags=request.tags
        )
        return ModelRegistryResponse.model_validate(model)

    async def list_models(
        self,
        algorithm: Optional[str] = Query(None, description="Filter by algorithm"),
        stage: Optional[str] = Query(None, description="Filter by stage"),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        stage_enum = ModelStageType(stage) if stage else None
        models = await control.list_all_models(algorithm=algorithm, stage=stage_enum)
        return ModelRegistryListResponse(
            models=[ModelRegistryResponse.model_validate(m) for m in models],
            total=len(models)
        )

    async def get_model(
        self,
        model_id: int,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        model = await control.get_model(model_id)
        return ModelRegistryResponse.model_validate(model)

    async def get_production_model(
        self,
        algorithm: Optional[str] = Query(None, description="Filter by algorithm"),
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        model = await control.get_production_model(algorithm=algorithm)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No production model found"
            )
        return ModelRegistryResponse.model_validate(model)

    async def update_model(
        self,
        model_id: int,
        request: ModelRegistryUpdateRequest,
        current_user: User = Depends(AuthGuard.require_admin),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        update_data = request.model_dump(exclude_unset=True)
        model = await control.update_model(model_id, **update_data)
        return ModelRegistryResponse.model_validate(model)

    async def update_model_stage(
        self,
        model_id: int,
        request: ModelStageUpdateRequest,
        current_user: User = Depends(AuthGuard.require_admin),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        model = await control.set_model_stage(model_id, request.stage)
        return ModelRegistryResponse.model_validate(model)

    async def promote_to_production(
        self,
        model_id: int,
        current_user: User = Depends(AuthGuard.require_admin),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        model = await control.promote_to_production(model_id)
        return ModelRegistryResponse.model_validate(model)

    async def activate_model(
        self,
        model_id: int,
        current_user: User = Depends(AuthGuard.require_admin),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        model = await control.toggle_model_active(model_id, True)
        return ModelRegistryResponse.model_validate(model)

    async def deactivate_model(
        self,
        model_id: int,
        current_user: User = Depends(AuthGuard.require_admin),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        model = await control.toggle_model_active(model_id, False)
        return ModelRegistryResponse.model_validate(model)

    async def delete_model(
        self,
        model_id: int,
        current_user: User = Depends(AuthGuard.require_admin),
        db: AsyncSession = Depends(get_async_db)
    ):
        control = ModelRegistryControl(db, current_user.user_id)
        await control.delete_model(model_id)

    async def predict_url(
        self,
        request: MLPredictRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        prediction_service = MLPredictionService(db)
        result = await prediction_service.predict_url(
            url=request.url,
            model_id=request.model_id
        )
        return MLPredictResponse(**result)

    async def predict_batch(
        self,
        request: MLBatchPredictRequest,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ):
        prediction_service = MLPredictionService(db)
        result = await prediction_service.predict_urls(
            urls=request.urls,
            model_id=request.model_id
        )
        return MLBatchPredictResponse(
            predictions=[MLPredictResponse(**p) for p in result['predictions']],
            total=result['total'],
            success_count=result['success_count'],
            error_count=result['error_count']
        )
