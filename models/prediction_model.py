from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


class PredictionModelDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: Optional[int] = None
    user_id: Optional[int] = None
    url: str

    accuracy_score: Optional[Decimal] = None
    recall_score: Optional[Decimal] = None
    precision_score: Optional[Decimal] = None
    f1_score: Optional[Decimal] = None

    suggested_desc: Optional[str] = Field(None, max_length=512)
    created_at: datetime = Field(default_factory=datetime.utcnow)
