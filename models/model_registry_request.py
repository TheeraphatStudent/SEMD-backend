"""Model Registry Request Models for API endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from decimal import Decimal
from libs.types.enums import ModelStageType


class ModelRegistryCreateRequest(BaseModel):
    name: str = Field(..., max_length=64, description="Model name")
    algorithm: str = Field(..., max_length=64, description="Algorithm used (e.g., xgboost, random_forest)")
    mlflow_run_id: str = Field(..., max_length=64, description="MLflow run ID")
    model_uri: str = Field(..., description="Path to model file")
    scaler_uri: str = Field(..., description="Path to scaler file")
    label_uri: str = Field(..., description="Path to label encoder file")
    selecter_uri: str = Field(default="", description="Path to feature selector file")
    mlflow_model_version: Optional[int] = Field(None, description="MLflow model version")
    experiment_id: Optional[str] = Field(None, max_length=64, description="MLflow experiment ID")
    stage: ModelStageType = Field(default=ModelStageType.NONE, description="Model stage")
    accuracy_score: Optional[Decimal] = Field(None, ge=0, le=1, description="Accuracy score")
    recall_score: Optional[Decimal] = Field(None, ge=0, le=1, description="Recall score")
    precision_score: Optional[Decimal] = Field(None, ge=0, le=1, description="Precision score")
    f1_score: Optional[Decimal] = Field(None, ge=0, le=1, description="F1 score")
    description: Optional[str] = Field(None, description="Model description")
    tags: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Model tags")


class ModelRegistryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    algorithm: Optional[str] = Field(None, max_length=64)
    mlflow_run_id: Optional[str] = Field(None, max_length=64)
    mlflow_model_version: Optional[int] = None
    experiment_id: Optional[str] = Field(None, max_length=64)
    stage: Optional[ModelStageType] = None
    model_uri: Optional[str] = None
    scaler_uri: Optional[str] = None
    label_uri: Optional[str] = None
    selecter_uri: Optional[str] = None
    accuracy_score: Optional[Decimal] = Field(None, ge=0, le=1)
    recall_score: Optional[Decimal] = Field(None, ge=0, le=1)
    precision_score: Optional[Decimal] = Field(None, ge=0, le=1)
    f1_score: Optional[Decimal] = Field(None, ge=0, le=1)
    description: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None


class ModelStageUpdateRequest(BaseModel):
    """Request model for updating model stage."""
    stage: ModelStageType = Field(..., description="New model stage")


class MLPredictRequest(BaseModel):
    """Request model for ML prediction."""
    url: str = Field(..., description="URL to predict")
    model_id: Optional[int] = Field(None, description="Specific model registry ID to use")


class MLBatchPredictRequest(BaseModel):
    """Request model for batch ML prediction."""
    urls: list[str] = Field(..., min_length=1, max_length=100, description="URLs to predict")
    model_id: Optional[int] = Field(None, description="Specific model registry ID to use")
