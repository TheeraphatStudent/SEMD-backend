# Model package

from .auth_model import AuthLoginRequest, AuthLoginProviderRequest, AuthTwoFactorRequest, AuthLoginResponse
from .base_response_model import BaseResponseModel
from .default_model import GetDefaultApiEndpoint ,GetDefaultHealthCheck
from .ml_model import MLModelItem, MLModelResponse
from .prediction_model import PredictionRequest, PredictionResponse, PredictionResult
from .report_model import ReportModelItem, ReportModelResponse, ReportModelRequest
from .stats import (
    ReportStatResponse, ReportStatListResponse, ReportStatTrendResponse,
    ReportDetailResponse, SystemStatResponse, SystemHealthResponse,
    SystemPerformanceResponse, PredictionStatResponse, PredictionTrendResponse,
    PredictionByModelResponse, PredictionDetailResponse, UserStatResponse,
    UserActivityResponse, UserRoleStatResponse, TopUserResponse,
    ApiKeyStatResponse, ApiKeyUsageResponse, ApiKeyTrendResponse,
    ApiEndpointStatResponse, ThirdPartyStatResponse, ThirdPartyServiceResponse,
    ThirdPartyTrendResponse, ThirdPartyErrorResponse, UrlFlagStatResponse,
    UrlFlagTrendResponse, UrlFlagDetailResponse, UrlFlagCategoryResponse
)

__all__ = [
    # Auth
    "AuthLoginRequest",
    "AuthLoginProviderRequest",
    "AuthTwoFactorRequest",
    "AuthLoginResponse",

    # Base
    "BaseResponseModel",

    # Default
    "GetDefaultApiEndpoint",
    "GetDefaultHealthCheck",

    # ML
    "MLModelItem",
    "MLModelResponse",

    # Prediction
    "PredictionRequest",
    "PredictionResponse",
    "PredictionResult",

    # Report
    "ReportModelItem",
    "ReportModelResponse",
    "ReportModelRequest",

    # Stats - Report
    "ReportStatResponse",
    "ReportStatListResponse",
    "ReportStatTrendResponse",
    "ReportDetailResponse",
    
    # Stats - System
    "SystemStatResponse",
    "SystemHealthResponse",
    "SystemPerformanceResponse",
    
    # Stats - Prediction
    "PredictionStatResponse",
    "PredictionTrendResponse",
    "PredictionByModelResponse",
    "PredictionDetailResponse",
    
    # Stats - User
    "UserStatResponse",
    "UserActivityResponse",
    "UserRoleStatResponse",
    "TopUserResponse",
    
    # Stats - API Key
    "ApiKeyStatResponse",
    "ApiKeyUsageResponse",
    "ApiKeyTrendResponse",
    "ApiEndpointStatResponse",
    
    # Stats - Third Party
    "ThirdPartyStatResponse",
    "ThirdPartyServiceResponse",
    "ThirdPartyTrendResponse",
    "ThirdPartyErrorResponse",
    
    # Stats - URL Flag
    "UrlFlagStatResponse",
    "UrlFlagTrendResponse",
    "UrlFlagDetailResponse",
    "UrlFlagCategoryResponse"
]