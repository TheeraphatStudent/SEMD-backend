# Routers package

from .base_route import BaseRoute
from .auth import AuthRoute
from .ml import MLRoute
from .prediction import PredictionRoute
from .report import ReportRoute
from .dashboard import DashboardRoute
from .setting import SettingRoute, ThirdServiceRoute, ServiceConfRoute
from .stat import (
    ReportStatRoute,
    PredictionStatRoute,
    UserStatRoute,
    ApiKeyStatRoute,
    ThirdPartyStatRoute,
    UrlFlagStatRoute
)

__all__ = [
    "BaseRoute",
    "AuthRoute",
    "MLRoute",
    "PredictionRoute",
    "ReportRoute",
    "DashboardRoute",
    "SettingRoute",
    "ThirdServiceRoute",
    "ServiceConfRoute",
    "ReportStatRoute",
    "PredictionStatRoute",
    "UserStatRoute",
    "ApiKeyStatRoute",
    "ThirdPartyStatRoute",
    "UrlFlagStatRoute"
]