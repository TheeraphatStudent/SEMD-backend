# Routers package

from .base_route import BaseRoute
from .auth import AuthRoute, UserRoute
from .ml import MLRoute
from .prediction import PredictionRoute
from .report import ReportRoute
from .dashboard import DashboardRoute
from .setting import SettingRoute, ThirdServiceRoute, ServiceConfRoute, UrlFlagRoute, AccessKeyRoute, SystemConfigRoute
from .queue import QueueRoute
from .stat import (
    ReportStatRoute,
    PredictionStatRoute,
    UserStatRoute,
    ApiKeyStatRoute,
    ThirdPartyStatRoute,
    UrlFlagStatRoute
)

__all__ = [
    'BaseRoute',
    'AuthRoute',
    'UserRoute',
    'MLRoute',
    'PredictionRoute',
    'ReportRoute',
    'DashboardRoute',
    'SettingRoute',
    'ThirdServiceRoute',
    'ServiceConfRoute',
    'UrlFlagRoute',
    'AccessKeyRoute',
    'SystemConfigRoute',
    'QueueRoute',
    'ReportStatRoute',
    'PredictionStatRoute',
    'UserStatRoute',
    'ApiKeyStatRoute',
    'ThirdPartyStatRoute',
    'UrlFlagStatRoute'
]
