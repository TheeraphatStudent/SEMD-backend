from pydantic import Field, BaseModel
from models import BaseResponseModel

class ReportStatItem(BaseModel):
  reported_by_amount: int = Field(
    title = "reported_by_amount",
    description = "ลิ้งค์ทีถูกรายงานโดยคุณ"
  )
  
  safe_urls: int = Field(
    title = "safe_urls",
    description = "ลิ้งค์ปลอดภัย"
  )

  malicious_urls: int = Field(
    title = "malicious_urls",
    description = "ลิ้งค์อันตราย"
  )
  
  error_urls: int = Field(
    title = "error_urls",
    description = "รายงานผิดพลาด"
  )
  
  pending_urls: int = Field(
    title = "pending_urls",
    description = "ลิ้งค์รอตรวจสอบ"
  )

class ReportStatResponse(BaseResponseModel):
  data: ReportStatItem

class ReportStatListItem(BaseModel):
  url: str = Field(
    title = "url",
    description = "URL อันตราย",
    examples = ["https://"]
  )

  amount: int = Field(
    title = "amount",
    description = "พบทั้งหมด 227 url",
    examples = [227]
  )

class ReportStatListResponse(BaseResponseModel):
  data: list[ReportStatListItem]

class ReportStatTrendItem(BaseModel):
  date: str = Field(
    title = "date",
    description = "เวลาของชุดข้อมูล",
    examples = ["10/04/2025"]
  )

  malicious_urls: int = Field(
    title = "malicious_urls",
    description = "ลิ้งค์อันตราย"
  )

  benign_urls: int = Field(
    title = "benign_urls",
    description = "ลิ้งค์ปลอดภัย"
  )

  pending_urls: int = Field(
    title = "pending_urls",
    description = "ลิ้งค์รอตรวจสอบ"
  )

class ReportStatTrendResponse(BaseResponseModel):
  data: list[ReportStatTrendItem]

class ReportDetailItem(BaseModel):
  id: str = Field(description="Report ID")
  url: str = Field(description="Reported URL")
  status: str = Field(description="Verification status: pending, verified, rejected")
  is_malicious: bool = Field(description="Whether URL is malicious")
  reported_by: str = Field(description="User ID who reported")
  reported_at: str = Field(description="Report timestamp")
  verified_by: str | None = Field(default=None, description="User ID who verified")
  verified_at: str | None = Field(default=None, description="Verification timestamp")

class ReportDetailResponse(BaseResponseModel):
  data: list[ReportDetailItem]
