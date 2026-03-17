"""Model Registry Response Models for API endpoints."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from libs.types.enums import ModelStageType


class ModelRegistryResponse(BaseModel):
    """Response model for model registry entry."""
    model_config = ConfigDict(from_attributes=True)

    model_registry_id: int
    service_conf_id: Optional[int] = None
    name: str
    algorithm: str
    mlflow_run_id: str
    mlflow_model_version: Optional[int] = None
    experiment_id: Optional[str] = None
    stage: str
    model_uri: str
    scaler_uri: str
    label_uri: str
    selecter_uri: str
    accuracy_score: Optional[Decimal] = None
    recall_score: Optional[Decimal] = None
    precision_score: Optional[Decimal] = None
    f1_score: Optional[Decimal] = None
    description: Optional[str] = None
    tags: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime


class ModelRegistryListResponse(BaseModel):
    models: List[ModelRegistryResponse]
    total: int


class MLPredictResponse(BaseModel):
    url: str
    prediction: str
    confidence: float
    probabilities: Optional[Dict[str, float]] = None
    model_id: int
    model_name: str
    algorithm: str


class MLBatchPredictResponse(BaseModel):
    predictions: List[MLPredictResponse]
    total: int
    success_count: int
    error_count: int
