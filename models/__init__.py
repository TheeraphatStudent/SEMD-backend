# Model package

from .auth_model import (
    AuthLoginRequest, AuthLoginProviderRequest, AuthTwoFactorRequest,
    AuthLoginResponse, TokenPairResponse, PreAuthResponse, TwoFAVerifyRequest,
    RefreshTokenRequest, TwoFASetupResponse, TwoFAEnableRequest,
    OAuthDeviceCodeRequest, OAuthDeviceCodeResponse, OAuthDevicePollRequest,
    OAuthAuthorizationRequest, OAuthAuthorizationResponse, OAuthCallbackRequest,
    RegisterRequest, RegisterResponse, CreateUserRequest, CreateUserResponse
)
from .base_response_model import BaseResponseModel
from .default_model import GetDefaultApiEndpoint, GetDefaultHealthCheck
from .prediction_model import PredictionModel as PredictionModelDb
from .user_model import UserModel as UserModelDb
from .refresh_model import RefreshTokenModel as RefreshTokenModelDb
from .service_conf_model import ServiceConfModel as ServiceConfModelDb
from .model_registry_model import ModelRegistryModel as ModelRegistryModelDb
from .access_key_model import AccessKeyModel as AccessKeyModelDb
from .url_flag_model import UrlFlagModel as UrlFlagModelDb
from .url_report_model import UrlReportModel as UrlReportModelDb
from .url_reported_model import UrlReportedModel as UrlReportedModelDb
from .url_report_request import UrlReportCreateRequest, UrlReportUpdateRequest
from .url_flag_request import UrlFlagCreateRequest, UrlFlagUpdateRequest
from .access_key_request import (
    AccessKeyCreateRequest, AccessKeyAdminCreateRequest, AccessKeyAdminUpdateRequest
)
from .user_request import (
    UserUpdateRequest, PasswordResetRequest,
    AdminCreateUserRequest, AdminUpdateUserRequest, AdminPasswordResetRequest
)
from .activity_log_model import ActivityLogModel as ActivityLogModelDb
from .usage_log_model import UsageLogModel as UsageLogModelDb
from .third_service_conf_model import ThirdServiceConfModel as ThirdServiceConfModelDb
from .third_service_model import (
    BodyTemplateItem, UrlTemplateConfig, ThirdServiceConfigJson,
    ThirdServiceCreateRequest, ThirdServiceUpdateRequest,
    ThirdServiceExecuteRequest, ThirdServiceResponse
)
from .prediction_response import PredictionResponse, PredictionDetailResponse
from .prediction_request import PredictionRequest
from .ml_response import MLServiceResponse
from .ml_message import (
    JobType, JobStatus, PredictionJobRequest, PredictionDetail,
    SinglePredictionResult, PredictionJobResult
)
from .report_response import ReportResponse, ReportListResponse
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
    "TokenPairResponse",
    "PreAuthResponse",
    "TwoFAVerifyRequest",
    "RefreshTokenRequest",
    "TwoFASetupResponse",
    "TwoFAEnableRequest",
    "OAuthDeviceCodeRequest",
    "OAuthDeviceCodeResponse",
    "OAuthDevicePollRequest",
    "OAuthAuthorizationRequest",
    "OAuthAuthorizationResponse",
    "OAuthCallbackRequest",
    "RegisterRequest",
    "RegisterResponse",
    "CreateUserRequest",
    "CreateUserResponse",

    # Base
    "BaseResponseModel",

    # Default
    "GetDefaultApiEndpoint",
    "GetDefaultHealthCheck",

    # Prediction
    "PredictionModelDb",
    "PredictionRequest",
    "PredictionResponse",
    "PredictionDetailResponse",
    
    # ML Message Protocol
    "JobType",
    "JobStatus",
    "PredictionJobRequest",
    "PredictionDetail",
    "SinglePredictionResult",
    "PredictionJobResult",

    # Report
    "ReportModelItem",
    "ReportModelResponse",
    "ReportModelRequest",
    
    "MLServiceResponse",
    "ReportResponse",
    "ReportListResponse",

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
    "UrlFlagCategoryResponse",
    
    # Database Models
    "UserModelDb",
    "RefreshTokenModelDb",
    "ServiceConfModelDb",
    "ModelRegistryModelDb",
    "AccessKeyModelDb",
    "UrlFlagModelDb",
    "UrlReportModelDb",
    "UrlReportedModelDb",
    "ActivityLogModelDb",
    "UsageLogModelDb",
    "ThirdServiceConfModelDb",
    
    # URL Report Request Models
    "UrlReportCreateRequest",
    "UrlReportUpdateRequest",
    
    # URL Flag Request Models
    "UrlFlagCreateRequest",
    "UrlFlagUpdateRequest",
    
    # Access Key Request Models
    "AccessKeyCreateRequest",
    "AccessKeyAdminCreateRequest",
    "AccessKeyAdminUpdateRequest",
    
    # User Request Models
    "UserUpdateRequest",
    "PasswordResetRequest",
    "AdminCreateUserRequest",
    "AdminUpdateUserRequest",
    "AdminPasswordResetRequest",
    
    # Third Service Models
    "BodyTemplateItem",
    "UrlTemplateConfig", 
    "ThirdServiceConfigJson",
    "ThirdServiceCreateRequest",
    "ThirdServiceUpdateRequest",
    "ThirdServiceExecuteRequest",
    "ThirdServiceResponse"
]