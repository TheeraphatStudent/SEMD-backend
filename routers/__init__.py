# Routers package
#
# `.base_route` MUST be imported before any router submodule (e.g. `.auth`)
# that does `from routers import BaseRoute` -- those submodules reach back
# into this partially-initialized package, so BaseRoute has to already be
# bound in this module's namespace first. ruff's import sort will alphabetize
# this block if run with --fix on this file; verify import order still
# satisfies that constraint after any auto-fix here (auth < base_route
# alphabetically, which is backwards).
from .base_route import BaseRoute  # noqa: I001 -- must precede .auth, see note above
from .auth import AuthRoute, UserRoute
from .dashboard import DashboardRoute
from .ml import MLRoute, MLTrainingRouter
from .prediction import PredictionRoute
from .queue import QueueRoute
from .report import ReportRoute
from .setting import AccessKeyRoute, ServiceConfRoute, SettingRoute, SystemConfigRoute, ThirdServiceRoute, UrlFlagRoute
from .stat import (
    ApiKeyStatRoute,
    PredictionStatRoute,
    ReportStatRoute,
    ThirdPartyStatRoute,
    UrlFlagStatRoute,
    UserStatRoute,
)

__all__ = [
    'BaseRoute',
    'AuthRoute',
    'UserRoute',
    'MLRoute',
    'MLTrainingRouter',
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
