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
    ML_MODEL = "ML_MODEL"
    REST_API = "REST_API"

class ModelStageType(str, Enum):
    NONE = "NONE"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"

class OAuthProviderType(str, Enum):
    # GITHUB removed: gh_id (the users.gh_id column used to look up/link a
    # GitHub-authenticated account) was dropped from the schema; Google is
    # the only supported login provider going forward.
    GOOGLE = "google"
