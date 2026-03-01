from pydantic import BaseModel, Field
from config.settings import settings

class GetDefaultApiEndpoint(BaseModel):
    message: str = Field(
        default=f"Welcome to {settings.app_name}", 
        description="Message"
    )
    version: str = Field(
        default=settings.app_version, 
        description="Version"
    )
    docs: str = Field(default="/docs", description="Docs")
    openapi: str = Field(default="/openapi.json", description="OpenAPI")

class GetDefaultHealthCheck(BaseModel):
    status: str = Field(default="Healthy", description="Status")
    cpu_usage: str = Field(default="0%", description="CPU Usage")
    memory_usage: str = Field(default="0 / 16GB", description="Memory Usage")
    disk_usage: str = Field(default="0 / 512GB", description="Disk Usage")