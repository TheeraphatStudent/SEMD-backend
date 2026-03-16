from pydantic import Field, BaseModel
from models import BaseResponseModel

class UrlFlagStatItem(BaseModel):
  total_flagged: int = Field(description="Total flagged URLs")
  pending_review: int = Field(description="URLs pending review")
  confirmed_malicious: int = Field(description="Confirmed malicious URLs")
  false_positives: int = Field(description="False positive flags")
  auto_flagged: int = Field(description="Auto-flagged by system")
  user_flagged: int = Field(description="Flagged by users")

class UrlFlagStatResponse(BaseResponseModel):
  data: UrlFlagStatItem

class UrlFlagTrendItem(BaseModel):
  date: str = Field(description="Date", examples=["2025-01-15"])
  total_flagged: int = Field(description="Total flags on this date")
  confirmed_malicious: int = Field(description="Confirmed malicious")
  false_positives: int = Field(description="False positives")
  pending_review: int = Field(description="Pending review")

class UrlFlagTrendResponse(BaseResponseModel):
  data: list[UrlFlagTrendItem]

class UrlFlagDetailItem(BaseModel):
  id: str = Field(description="Flag ID")
  url: str = Field(description="Flagged URL")
  flag_type: str = Field(description="Flag type: phishing, malware, spam, etc")
  status: str = Field(description="Status: pending, confirmed, rejected")
  flagged_by: str = Field(description="User ID or system")
  flagged_at: str = Field(description="Flag timestamp")
  reviewed_by: str | None = Field(default=None, description="Reviewer ID")
  reviewed_at: str | None = Field(default=None, description="Review timestamp")
  confidence: float = Field(description="Confidence score")

class UrlFlagDetailResponse(BaseResponseModel):
  data: list[UrlFlagDetailItem]

class UrlFlagCategoryItem(BaseModel):
  category: str = Field(description="Flag category: phishing, malware, spam, etc")
  count: int = Field(description="Number of flags in this category")
  percentage: float = Field(description="Percentage of total flags")

class UrlFlagCategoryResponse(BaseResponseModel):
  data: list[UrlFlagCategoryItem]
