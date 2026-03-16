from pydantic import Field, BaseModel
from models import BaseResponseModel

class PredictionStatItem(BaseModel):
  total_predictions: int = Field(description="Total number of predictions")
  malicious_count: int = Field(description="Number of malicious URLs detected")
  safe_count: int = Field(description="Number of safe URLs")
  pending_count: int = Field(description="Number of pending predictions")
  accuracy_rate: float = Field(description="Overall accuracy rate")
  avg_response_time: float = Field(description="Average response time in ms")

class PredictionStatResponse(BaseResponseModel):
  data: PredictionStatItem

class PredictionTrendItem(BaseModel):
  date: str = Field(description="Date of data point", examples=["2025-01-15"])
  total_predictions: int = Field(description="Total predictions on this date")
  malicious_count: int = Field(description="Malicious URLs detected")
  safe_count: int = Field(description="Safe URLs detected")
  accuracy_rate: float = Field(description="Accuracy rate for this date")

class PredictionTrendResponse(BaseResponseModel):
  data: list[PredictionTrendItem]

class PredictionByModelItem(BaseModel):
  model_id: str = Field(description="ML model ID")
  model_name: str = Field(description="ML model name")
  prediction_count: int = Field(description="Number of predictions")
  accuracy_rate: float = Field(description="Model accuracy rate")
  avg_response_time: float = Field(description="Average response time in ms")

class PredictionByModelResponse(BaseResponseModel):
  data: list[PredictionByModelItem]

class PredictionDetailItem(BaseModel):
  id: str = Field(description="Prediction ID")
  url: str = Field(description="Predicted URL")
  is_malicious: bool = Field(description="Prediction result")
  confidence: float = Field(description="Confidence score")
  model_used: str = Field(description="Model ID used")
  predicted_at: str = Field(description="Prediction timestamp")
  response_time: float = Field(description="Response time in ms")

class PredictionDetailResponse(BaseResponseModel):
  data: list[PredictionDetailItem]
