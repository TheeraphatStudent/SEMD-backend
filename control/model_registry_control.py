"""Model Registry Control - Business logic layer for model registry operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from decimal import Decimal

from services.model_registry_service import ModelRegistryService
from models.db import ModelRegistry
from libs.types.enums import ModelStageType


class ModelRegistryControl:
    def __init__(self, db: AsyncSession, user_id: int):
        self.service = ModelRegistryService(db)
        self.user_id = user_id

    async def create_model(
        self,
        name: str,
        algorithm: str,
        mlflow_run_id: str,
        model_uri: str,
        scaler_uri: str,
        label_uri: str,
        selecter_uri: str = "",
        mlflow_model_version: Optional[int] = None,
        experiment_id: Optional[str] = None,
        stage: ModelStageType = ModelStageType.NONE,
        accuracy_score: Optional[Decimal] = None,
        recall_score: Optional[Decimal] = None,
        precision_score: Optional[Decimal] = None,
        f1_score: Optional[Decimal] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> ModelRegistry:
        return await self.service.create_model_registry(
            user_id=self.user_id,
            name=name,
            algorithm=algorithm,
            mlflow_run_id=mlflow_run_id,
            model_uri=model_uri,
            scaler_uri=scaler_uri,
            label_uri=label_uri,
            selecter_uri=selecter_uri,
            mlflow_model_version=mlflow_model_version,
            experiment_id=experiment_id,
            stage=stage,
            accuracy_score=accuracy_score,
            recall_score=recall_score,
            precision_score=precision_score,
            f1_score=f1_score,
            description=description,
            tags=tags
        )

    async def get_model(self, model_registry_id: int) -> ModelRegistry:
        return await self.service.get_model_registry(model_registry_id)

    async def get_model_by_name(self, name: str) -> Optional[ModelRegistry]:
        return await self.service.get_model_by_name(name)

    async def list_models(
        self,
        algorithm: Optional[str] = None,
        stage: Optional[ModelStageType] = None
    ) -> List[ModelRegistry]:
        return await self.service.list_models(
            user_id=self.user_id,
            algorithm=algorithm,
            stage=stage
        )

    async def list_all_models(
        self,
        algorithm: Optional[str] = None,
        stage: Optional[ModelStageType] = None
    ) -> List[ModelRegistry]:
        """List all models (admin only)."""
        return await self.service.list_models(
            user_id=None,
            algorithm=algorithm,
            stage=stage
        )

    async def list_active_models(self) -> List[ModelRegistry]:
        return await self.service.list_active_models(user_id=self.user_id)

    async def get_production_model(self, algorithm: Optional[str] = None) -> Optional[ModelRegistry]:
        return await self.service.get_production_model(algorithm=algorithm)

    async def update_model(
        self,
        model_registry_id: int,
        **kwargs
    ) -> ModelRegistry:
        return await self.service.update_model_registry(
            model_registry_id=model_registry_id,
            **kwargs
        )

    async def set_model_stage(
        self,
        model_registry_id: int,
        stage: ModelStageType
    ) -> ModelRegistry:
        return await self.service.set_model_stage(model_registry_id, stage)

    async def promote_to_production(self, model_registry_id: int) -> ModelRegistry:
        return await self.service.promote_to_production(model_registry_id)

    async def delete_model(self, model_registry_id: int) -> None:
        return await self.service.delete_model_registry(model_registry_id)

    async def toggle_model_active(
        self,
        model_registry_id: int,
        is_active: bool
    ) -> ModelRegistry:
        return await self.service.toggle_model_active(model_registry_id, is_active)
