from pydantic import Field, BaseModel
from models import BaseResponseModel

class ApiKeyStatItem(BaseModel):
  total_keys: int = Field(description="Total number of API keys")
  active_keys: int = Field(description="Active API keys")
  expired_keys: int = Field(description="Expired API keys")
  revoked_keys: int = Field(description="Revoked API keys")
  total_requests: int = Field(description="Total API requests")
  requests_today: int = Field(description="API requests today")

class ApiKeyStatResponse(BaseResponseModel):
  data: ApiKeyStatItem

class ApiKeyUsageItem(BaseModel):
  api_key_id: str = Field(description="API key ID")
  key_name: str = Field(description="API key name")
  owner: str = Field(description="Key owner")
  request_count: int = Field(description="Number of requests")
  last_used: str = Field(description="Last used timestamp")
  status: str = Field(description="Key status: active, expired, revoked")

class ApiKeyUsageResponse(BaseResponseModel):
  data: list[ApiKeyUsageItem]

class ApiKeyTrendItem(BaseModel):
  date: str = Field(description="Date", examples=["2025-01-15"])
  request_count: int = Field(description="Number of API requests")
  unique_keys: int = Field(description="Number of unique keys used")
  error_count: int = Field(description="Number of errors")

class ApiKeyTrendResponse(BaseResponseModel):
  data: list[ApiKeyTrendItem]

class ApiEndpointStatItem(BaseModel):
  endpoint: str = Field(description="API endpoint path")
  method: str = Field(description="HTTP method")
  request_count: int = Field(description="Number of requests")
  avg_response_time: float = Field(description="Average response time in ms")
  error_rate: float = Field(description="Error rate percentage")

class ApiEndpointStatResponse(BaseResponseModel):
  data: list[ApiEndpointStatItem]
