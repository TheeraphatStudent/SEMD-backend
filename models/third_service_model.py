from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import re


class BodyTemplateItem(BaseModel):
    key: str = Field(..., description="Key name in the request body")
    input: str = Field(..., description="Input variable name to map from runtime vars")
    
class UrlTemplateConfig(BaseModel):
    path_params: Dict[str, str] = Field(
        default_factory=dict,
        description="Path parameters mapping: {'param_name': 'input_var_name'}"
    )
    query_params: Dict[str, str] = Field(
        default_factory=dict,
        description="Query parameters mapping: {'param_name': 'input_var_name'}"
    )

class ThirdServiceConfigJson(BaseModel):
    body_template: List[BodyTemplateItem] = Field(
        default_factory=list,
        description="Body template mapping for POST/PUT requests"
    )
    url_template: UrlTemplateConfig = Field(
        default_factory=UrlTemplateConfig,
        description="URL template config for dynamic path and query params"
    )
    response_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Response field mapping to standardize output"
    )


class ServiceConfModelDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    service_conf_id: Optional[int] = None
    user_id: Optional[int] = None
    service_name: str = Field(..., max_length=32)
    service_type: str = Field(..., max_length=20)
    is_active: bool = True
    version_no: str = Field(..., max_length=12)
    config_uri: str
    config_json: dict = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ThirdServiceConfModelDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    third_service_conf_id: Optional[int] = None
    service_conf_id: Optional[int] = None
    service_name: str = Field(..., max_length=64)
    base_url: str
    http_method: str = Field(default="GET", max_length=8)
    headers_json: dict = {}
    config_json: dict = {}
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ThirdServiceCreateRequest(BaseModel):
    service_name: str = Field(..., max_length=64, example="Cloudflare URL Scanner")
    base_url: str = Field(
        ..., 
        description="Base URL with optional {{variable}} placeholders",
        example="https://api.cloudflare.com/client/v4/accounts/{{account_id}}/urlscanner/v2/scan"
    )
    http_method: str = Field(default="POST", max_length=8)
    headers_json: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP headers including authentication (e.g., Authorization, API keys)",
        example={"Content-Type": "application/json", "Authorization": "Bearer your_token_here"}
    )
    config_json: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration for body template and URL template",
        example={
            "body_template": [{"key": "url", "input": "url"}],
            "url_template": {
                "path_params": {"account_id": "your_account_id"},
                "query_params": {"url": "url"}
            },
            "response_mapping": {"is_malicious": "result.malicious"}
        }
    )

class ThirdServiceUpdateRequest(BaseModel):
    service_name: Optional[str] = Field(None, max_length=64)
    base_url: Optional[str] = None
    http_method: Optional[str] = Field(None, max_length=8)
    headers_json: Optional[Dict[str, str]] = None
    config_json: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ThirdServiceExecuteRequest(BaseModel):
    vars: dict = Field(..., description="Runtime variables to resolve body template")

class ThirdServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    third_service_conf_id: int
    service_conf_id: Optional[int] = None
    service_name: str
    base_url: str
    http_method: str
    headers_json: dict
    config_json: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
