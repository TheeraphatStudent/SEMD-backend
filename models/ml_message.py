from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    PREDICTION = "prediction"
    BATCH_PREDICTION = "batch_prediction"
    TRAINING = "training"


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PredictionJobRequest(BaseModel):
    job_id: str
    job_type: JobType = JobType.PREDICTION
    url: Optional[str] = None
    urls: Optional[List[str]] = None
    user_id: Optional[int] = None
    model_id: Optional[str] = None
    compare: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PredictionDetail(BaseModel):
    predicted_class: str
    is_malicious: bool
    confidence: float
    probabilities: Optional[Dict[str, float]] = None


class SinglePredictionResult(BaseModel):
    status: str
    url: str
    prediction: Optional[PredictionDetail] = None
    suggested_desc: Optional[str] = None
    error: Optional[str] = None
    model_id: Optional[str] = None
    prediction_id: Optional[int] = None
    features: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class PredictionJobResult(BaseModel):
    job_id: str
    job_type: str
    status: JobStatus
    url: Optional[str] = None
    urls: Optional[List[str]] = None
    prediction: Optional[PredictionDetail] = None
    suggested_desc: Optional[str] = None
    results: Optional[List[SinglePredictionResult]] = None
    total: Optional[int] = None
    successful: Optional[int] = None
    failed: Optional[int] = None
    error: Optional[str] = None
    model_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
