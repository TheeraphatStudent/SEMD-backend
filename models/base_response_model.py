from pydantic import BaseModel, Field

class BaseResponseModel(BaseModel):
    status: int = Field(
        title="status",
        description="Response status code",
        examples=[200, 404, 500],
    )
    message: str = Field(
        title="message",
        description="Response message",
        examples=["Success", "Not found", "Internal server error"],
    )

class ErrorResponse422(BaseResponseModel):
    status: int = 422
    message: str = "Unprocessable Content"
    strace: str = Field(
        title="strace",
        description="Stack trace",
        examples=["Traceback (most recent call last):"],
    )