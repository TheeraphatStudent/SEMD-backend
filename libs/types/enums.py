from enum import Enum

class RoleType(str, Enum):
    GUEST = "GUEST"
    MEMBER = "MEMBER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"

class FlagType(str, Enum):
    MALICIOUS = "MALICIOUS"
    BENIGN = "BENIGN"

class ACLType(str, Enum):
    GLOBAL = "GLOBAL"
    PRIVATE = "PRIVATE"

class ReportStatusType(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class UsageLogType(str, Enum):
    PREDICT = "PREDICT"
    ACCESS_KEY = "ACCESS_KEY"

class ServiceType(str, Enum):
    REST_API = "REST_API"
    WEB_HOOK = "WEB_HOOK"
    SDK = "SDK"

class ModelStageType(str, Enum):
    NONE = "NONE"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"
