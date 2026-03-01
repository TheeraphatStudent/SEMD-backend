from pydantic import Field, BaseModel
from models import BaseResponseModel

class SystemStatItem(BaseModel):
  total_model: int = Field(
    title = "models",
    description = "โมเดล"
  )

  total_queue: int = Field(
    title = "queues",
    description = "คิว"
  )

  total_api_key: int = Field(
    title = "api_keys",
    description = "API access key"
  )

  total_user: int = Field(
    title = "users",
    description = "ผู้ใช้งานทั้งหมด"
  )

  total_dataset: int = Field(
    title = "datasets",
    description = "ชุดข้อมูล"
  )

class SystemStatResponse(BaseResponseModel):
  data: SystemStatItem

class SystemHealthItem(BaseModel):
  status: str = Field(description="System status: healthy, degraded, down")
  cpu_usage: float = Field(description="CPU usage percentage")
  memory_usage: float = Field(description="Memory usage percentage")
  disk_usage: float = Field(description="Disk usage percentage")
  uptime: int = Field(description="System uptime in seconds")
  active_connections: int = Field(description="Active database connections")

class SystemHealthResponse(BaseResponseModel):
  data: SystemHealthItem

class SystemPerformanceItem(BaseModel):
  timestamp: str = Field(description="Timestamp of measurement")
  cpu_usage: float = Field(description="CPU usage percentage")
  memory_usage: float = Field(description="Memory usage percentage")
  request_count: int = Field(description="Number of requests")
  avg_response_time: float = Field(description="Average response time in ms")

class SystemPerformanceResponse(BaseResponseModel):
  data: list[SystemPerformanceItem]
