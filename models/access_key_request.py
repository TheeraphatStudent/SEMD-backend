from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AccessKeyCreateRequest(BaseModel):
    key_name: Optional[str] = Field(
        None, max_length=64, description='Name for the access key')
    expired_at: Optional[datetime] = Field(
        None, description='Expiration date for the key')


class AccessKeyAdminCreateRequest(BaseModel):
    user_id: int = Field(..., description='User ID to create key for')
    key_name: Optional[str] = Field(
        None, max_length=64, description='Name for the access key')
    usage_limit: Optional[int] = Field(
        None, ge=0, description='Usage limit for the key (null = unlimited)')
    expired_at: Optional[datetime] = Field(
        None, description='Expiration date for the key')


class AccessKeyAdminUpdateRequest(BaseModel):
    key_name: Optional[str] = Field(
        None, max_length=64, description='Name for the access key')
    usage_limit: Optional[int] = Field(
        None, ge=0, description='Usage limit for the key (null = unlimited)')
    is_active: Optional[bool] = Field(
        None, description='Whether the key is active')
    expired_at: Optional[datetime] = Field(
        None, description='Expiration date for the key')


class UsageStatQuery(BaseModel):
    year: int = Field(..., ge=2020, description='Year to query')
    month: Optional[int] = Field(
        None, ge=1, le=12, description='Month to query (1-12)')
