"""
Model Registry Service - CRUD operations for ML model registry.
Supports both local model files and MLflow model registry integration.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from fastapi import HTTPException, status
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from models.db import ModelRegistry, ServiceConf
from libs.types.enums import ServiceType, ModelStageType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelRegistryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_model_registry(
        self,
        user_id: int,
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
        """Create a new model registry entry with associated service configuration."""
        
        service_conf = ServiceConf(
            user_id=user_id,
            service_name=name,
            service_type=ServiceType.ML_MODEL.value,
            is_active=True,
            version_no='1.0.0',
            config_uri=model_uri,
            config_json={
                'algorithm': algorithm,
                'mlflow_run_id': mlflow_run_id,
                'model_uri': model_uri,
                'scaler_uri': scaler_uri,
                'label_uri': label_uri
            }
        )
        self.db.add(service_conf)
        await self.db.flush()
        await self.db.refresh(service_conf)

        model_registry = ModelRegistry(
            service_conf_id=service_conf.service_conf_id,
            name=name,
            algorithm=algorithm,
            mlflow_run_id=mlflow_run_id,
            mlflow_model_version=mlflow_model_version,
            experiment_id=experiment_id,
            stage=stage.value if isinstance(stage, ModelStageType) else stage,
            model_uri=model_uri,
            scaler_uri=scaler_uri,
            label_uri=label_uri,
            selecter_uri=selecter_uri,
            accuracy_score=accuracy_score,
            recall_score=recall_score,
            precision_score=precision_score,
            f1_score=f1_score,
            description=description,
            tags=tags or {}
        )
        self.db.add(model_registry)
        await self.db.commit()
        await self.db.refresh(model_registry)

        logger.info(f"Created model registry: {name} (ID: {model_registry.model_registry_id})")
        return model_registry

    async def get_model_registry(self, model_registry_id: int) -> ModelRegistry:
        """Get a model registry entry by ID."""
        stmt = select(ModelRegistry).where(
            ModelRegistry.model_registry_id == model_registry_id
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model registry {model_registry_id} not found"
            )

        return model

    async def get_model_by_service_conf(self, service_conf_id: int) -> Optional[ModelRegistry]:
        """Get model registry by service configuration ID."""
        stmt = select(ModelRegistry).where(
            ModelRegistry.service_conf_id == service_conf_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_model_by_name(self, name: str) -> Optional[ModelRegistry]:
        """Get model registry by name."""
        stmt = select(ModelRegistry).where(ModelRegistry.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_models(
        self,
        user_id: Optional[int] = None,
        algorithm: Optional[str] = None,
        stage: Optional[ModelStageType] = None
    ) -> List[ModelRegistry]:
        """List all model registry entries with optional filters."""
        stmt = select(ModelRegistry).join(
            ServiceConf,
            ServiceConf.service_conf_id == ModelRegistry.service_conf_id
        )

        if user_id is not None:
            stmt = stmt.where(ServiceConf.user_id == user_id)

        if algorithm:
            stmt = stmt.where(ModelRegistry.algorithm == algorithm)

        if stage:
            stage_value = stage.value if isinstance(stage, ModelStageType) else stage
            stmt = stmt.where(ModelRegistry.stage == stage_value)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_active_models(self, user_id: Optional[int] = None) -> List[ModelRegistry]:
        """List all active model registry entries."""
        stmt = select(ModelRegistry).join(
            ServiceConf,
            ServiceConf.service_conf_id == ModelRegistry.service_conf_id
        ).where(ServiceConf.is_active == True)

        if user_id is not None:
            stmt = stmt.where(ServiceConf.user_id == user_id)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_production_model(self, algorithm: Optional[str] = None) -> Optional[ModelRegistry]:
        """Get the production model (highest priority active model)."""
        stmt = select(ModelRegistry).join(
            ServiceConf,
            ServiceConf.service_conf_id == ModelRegistry.service_conf_id
        ).where(
            ServiceConf.is_active == True,
            ModelRegistry.stage == ModelStageType.PRODUCTION.value
        )

        if algorithm:
            stmt = stmt.where(ModelRegistry.algorithm == algorithm)

        stmt = stmt.order_by(ModelRegistry.f1_score.desc()).limit(1)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_model_registry(
        self,
        model_registry_id: int,
        name: Optional[str] = None,
        algorithm: Optional[str] = None,
        mlflow_run_id: Optional[str] = None,
        mlflow_model_version: Optional[int] = None,
        experiment_id: Optional[str] = None,
        stage: Optional[ModelStageType] = None,
        model_uri: Optional[str] = None,
        scaler_uri: Optional[str] = None,
        label_uri: Optional[str] = None,
        selecter_uri: Optional[str] = None,
        accuracy_score: Optional[Decimal] = None,
        recall_score: Optional[Decimal] = None,
        precision_score: Optional[Decimal] = None,
        f1_score: Optional[Decimal] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> ModelRegistry:
        """Update a model registry entry."""
        model = await self.get_model_registry(model_registry_id)

        update_data = {}
        if name is not None:
            update_data['name'] = name
        if algorithm is not None:
            update_data['algorithm'] = algorithm
        if mlflow_run_id is not None:
            update_data['mlflow_run_id'] = mlflow_run_id
        if mlflow_model_version is not None:
            update_data['mlflow_model_version'] = mlflow_model_version
        if experiment_id is not None:
            update_data['experiment_id'] = experiment_id
        if stage is not None:
            update_data['stage'] = stage.value if isinstance(stage, ModelStageType) else stage
        if model_uri is not None:
            update_data['model_uri'] = model_uri
        if scaler_uri is not None:
            update_data['scaler_uri'] = scaler_uri
        if label_uri is not None:
            update_data['label_uri'] = label_uri
        if selecter_uri is not None:
            update_data['selecter_uri'] = selecter_uri
        if accuracy_score is not None:
            update_data['accuracy_score'] = accuracy_score
        if recall_score is not None:
            update_data['recall_score'] = recall_score
        if precision_score is not None:
            update_data['precision_score'] = precision_score
        if f1_score is not None:
            update_data['f1_score'] = f1_score
        if description is not None:
            update_data['description'] = description
        if tags is not None:
            update_data['tags'] = tags

        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            stmt = (
                update(ModelRegistry)
                .where(ModelRegistry.model_registry_id == model_registry_id)
                .values(**update_data)
            )
            await self.db.execute(stmt)
            await self.db.commit()
            await self.db.refresh(model)

        logger.info(f"Updated model registry: {model_registry_id}")
        return model

    async def set_model_stage(
        self,
        model_registry_id: int,
        stage: ModelStageType
    ) -> ModelRegistry:
        """Set the stage of a model registry entry."""
        return await self.update_model_registry(
            model_registry_id=model_registry_id,
            stage=stage
        )

    async def promote_to_production(self, model_registry_id: int) -> ModelRegistry:
        """Promote a model to production stage."""
        model = await self.get_model_registry(model_registry_id)

        # Demote current production models of the same algorithm
        stmt = (
            update(ModelRegistry)
            .where(
                ModelRegistry.algorithm == model.algorithm,
                ModelRegistry.stage == ModelStageType.PRODUCTION.value,
                ModelRegistry.model_registry_id != model_registry_id
            )
            .values(stage=ModelStageType.ARCHIVED.value, updated_at=datetime.utcnow())
        )
        await self.db.execute(stmt)

        # Promote the selected model
        return await self.set_model_stage(model_registry_id, ModelStageType.PRODUCTION)

    async def delete_model_registry(self, model_registry_id: int) -> None:
        """Delete a model registry entry and its associated service configuration."""
        model = await self.get_model_registry(model_registry_id)
        service_conf_id = model.service_conf_id

        # Delete model registry
        stmt = delete(ModelRegistry).where(
            ModelRegistry.model_registry_id == model_registry_id
        )
        await self.db.execute(stmt)

        # Delete associated service configuration
        if service_conf_id:
            stmt = delete(ServiceConf).where(
                ServiceConf.service_conf_id == service_conf_id
            )
            await self.db.execute(stmt)

        await self.db.commit()
        logger.info(f"Deleted model registry: {model_registry_id}")

    async def toggle_model_active(
        self,
        model_registry_id: int,
        is_active: bool
    ) -> ModelRegistry:
        """Toggle the active status of a model's service configuration."""
        model = await self.get_model_registry(model_registry_id)

        if model.service_conf_id:
            stmt = (
                update(ServiceConf)
                .where(ServiceConf.service_conf_id == model.service_conf_id)
                .values(is_active=is_active, updated_at=datetime.utcnow())
            )
            await self.db.execute(stmt)
            await self.db.commit()

        return model
