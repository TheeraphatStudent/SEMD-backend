from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from libs.types.enums import ModelStageType

class ModelRegistryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    model_registry_id: Optional[int] = None
    service_conf_id: Optional[int] = None
    name: str = Field(..., max_length=64)
    algorithm: str = Field(..., max_length=64)
    
    mlflow_run_id: str = Field(..., max_length=64)
    mlflow_model_version: Optional[int] = None
    experiment_id: Optional[str] = Field(None, max_length=64)
    stage: ModelStageType = ModelStageType.NONE
    
    model_uri: str
    scaler_uri: str
    label_uri: str
    selecter_uri: str
    
    accuracy_score: Optional[Decimal] = None
    recall_score: Optional[Decimal] = None
    precision_score: Optional[Decimal] = None
    f1_score: Optional[Decimal] = None
    
    description: Optional[str] = None
    tags: dict = {}
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
