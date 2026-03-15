from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PredictByInfo(BaseModel):
    user_id: Optional[int] = None
    profile_img_url: Optional[str] = None
    username: Optional[str] = None


class QueueItem(BaseModel):
    url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    predict_by: PredictByInfo


class QueueItemResponse(BaseModel):
    url: str
    created_at: str
    predict_by: PredictByInfo
