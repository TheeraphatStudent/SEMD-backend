from pydantic import Field, BaseModel
from models import BaseResponseModel

class ThirdPartyStatItem(BaseModel):
  total_services: int = Field(description="Total third-party services")
  active_services: int = Field(description="Active services")
  inactive_services: int = Field(description="Inactive services")
  total_requests: int = Field(description="Total requests to third-party services")
  successful_requests: int = Field(description="Successful requests")
  failed_requests: int = Field(description="Failed requests")

class ThirdPartyStatResponse(BaseResponseModel):
  data: ThirdPartyStatItem

class ThirdPartyServiceItem(BaseModel):
  service_id: str = Field(description="Service ID")
  service_name: str = Field(description="Service name")
  service_type: str = Field(description="Service type: url_scanner, threat_intel, etc")
  status: str = Field(description="Service status: active, inactive, error")
  request_count: int = Field(description="Number of requests")
  success_rate: float = Field(description="Success rate percentage")
  avg_response_time: float = Field(description="Average response time in ms")
  last_used: str = Field(description="Last used timestamp")

class ThirdPartyServiceResponse(BaseResponseModel):
  data: list[ThirdPartyServiceItem]

class ThirdPartyTrendItem(BaseModel):
  date: str = Field(description="Date", examples=["2025-01-15"])
  service_name: str = Field(description="Service name")
  request_count: int = Field(description="Number of requests")
  success_count: int = Field(description="Successful requests")
  failed_count: int = Field(description="Failed requests")
  avg_response_time: float = Field(description="Average response time in ms")

class ThirdPartyTrendResponse(BaseResponseModel):
  data: list[ThirdPartyTrendItem]

class ThirdPartyErrorItem(BaseModel):
  service_name: str = Field(description="Service name")
  error_type: str = Field(description="Error type")
  error_message: str = Field(description="Error message")
  count: int = Field(description="Number of occurrences")
  last_occurred: str = Field(description="Last occurrence timestamp")

class ThirdPartyErrorResponse(BaseResponseModel):
  data: list[ThirdPartyErrorItem]
