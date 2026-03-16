from pydantic import Field, BaseModel
from typing import Optional
from fastapi import UploadFile


class PredictionRequest(BaseModel):
    url: Optional[str | list[str]] = Field(
        None,
        title='url',
        description="URL to predict -> 'https://example.com' or ['http://example.com', 'https://test.com']"
    )
    text_file: Optional[UploadFile] = Field(
        None,
        description='Upload a text file with URLs, one per line'
    )
    csv_file: Optional[UploadFile] = Field(
        None,
        description="Upload a CSV file with URLs in the first column or 'url' column"
    )
    service_id: Optional[int] = Field(
        None,
        description='Service ID to use for predictor',
        example=1
    )
