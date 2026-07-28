import uuid

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    UUID,
    BigInteger,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(32), unique=True, nullable=False)
    email = Column(String(64), unique=True, nullable=False)
    full_name = Column(String(512), nullable=False)
    birthday = Column(TIMESTAMP(timezone=True), nullable=True)
    password_hash = Column(String(1024), nullable=False)
    role = Column(String(20), nullable=False, default='MEMBER')

    gg_id = Column(Text, nullable=True)
    gg_acc_token = Column(Text, nullable=True)
    gh_acc_token = Column(Text, nullable=True)
    gh_re_token = Column(Text, nullable=True)
    twofa_secret = Column(Text, nullable=True)
    is_2fa_enabled = Column(Boolean, nullable=False, server_default='false')

    ex_acc_token = Column(Text, nullable=True)
    ex_acc_token_exp = Column(TIMESTAMP(timezone=True), nullable=True)
    profile_img_uri = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now())


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    refresh_tokens_id = Column(
        BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False)
    jti = Column(UUID(as_uuid=True), unique=True,
                 nullable=False, default=uuid.uuid4)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    is_revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())


class ServiceConf(Base):
    __tablename__ = 'service_conf'

    service_conf_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)
    service_name = Column(String(32), nullable=False)
    service_type = Column(
        Enum('REST_API', 'ML_MODEL', name='service_type'), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    version_no = Column(String(12), nullable=False)
    config_uri = Column(Text, nullable=False)
    config_json = Column(JSON, nullable=False, default={})
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now())


class ModelRegistry(Base):
    __tablename__ = 'model_registry'

    model_registry_id = Column(
        BigInteger, primary_key=True, autoincrement=True)
    service_conf_id = Column(
        BigInteger, ForeignKey('service_conf.service_conf_id', ondelete='CASCADE'), unique=True, nullable=True)
    name = Column(String(64), nullable=False)
    algorithm = Column(String(64), nullable=False)

    mlflow_run_id = Column(String(64), nullable=False)
    mlflow_model_version = Column(Integer, nullable=True)
    experiment_id = Column(String(64), nullable=True)
    stage = Column(String(20), nullable=False, default='NONE')

    model_uri = Column(Text, nullable=False)
    scaler_uri = Column(Text, nullable=False)
    label_uri = Column(Text, nullable=False)
    selecter_uri = Column(Text, nullable=False)

    accuracy_score = Column(Numeric(5, 4), nullable=True)
    recall_score = Column(Numeric(5, 4), nullable=True)
    precision_score = Column(Numeric(5, 4), nullable=True)
    f1_score = Column(Numeric(5, 4), nullable=True)

    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=False, default={})

    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now())


class AccessKey(Base):
    __tablename__ = 'access_key'

    access_key_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)
    key_name = Column(String(64), nullable=True)
    access_key_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    usage_limit = Column(BigInteger, nullable=True)
    expired_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now())


class Prediction(Base):
    __tablename__ = 'prediction'

    prediction_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    url = Column(Text, nullable=False)

    accuracy_score = Column(Numeric(10, 2), nullable=True)
    recall_score = Column(Numeric(10, 2), nullable=True)
    precision_score = Column(Numeric(10, 2), nullable=True)
    f1_score = Column(Numeric(10, 2), nullable=True)

    is_malicious = Column(Boolean, nullable=False)
    predict_class = Column(String(64), nullable=False)

    suggested_desc = Column(String(512), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())


class UrlFlag(Base):
    __tablename__ = 'url_flag'

    url_flag_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)
    url = Column(Text, nullable=False)
    type = Column(String(20), nullable=False, default='BENIGN')
    access_level = Column(String(20), nullable=False, default='PRIVATE')
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now())


class UrlReport(Base):
    __tablename__ = 'url_report'

    url_report_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=True)
    url = Column(Text, nullable=False)
    categories = Column(String(20), nullable=False, default='BENIGN')
    status = Column(String(20), nullable=False, default='PENDING')
    remark = Column(String(256), nullable=True)
    reviewed_by = Column(BigInteger, ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now())


class ActivityLog(Base):
    __tablename__ = 'activity_log'

    activity_log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    method = Column(String(16), nullable=False)
    endpoint = Column(String(1024), nullable=False)
    request_id = Column(String(32), unique=True, nullable=False)
    client_ip = Column(String(32), nullable=True)
    client_agent = Column(String(256), nullable=True)
    response = Column(String(512), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now())


class UsageLog(Base):
    __tablename__ = 'usage_log'

    usage_log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_id = Column(
        BigInteger, ForeignKey('service_conf.service_conf_id', ondelete='SET NULL'), nullable=True)
    access_key_id = Column(
        BigInteger, ForeignKey('access_key.access_key_id', ondelete='SET NULL'), nullable=True)
    prediction_id = Column(
        BigInteger, ForeignKey('prediction.prediction_id', ondelete='SET NULL'), nullable=True)
    type = Column(Enum('PREDICT', 'ACCESS_KEY',
                  name='usage_log_type'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())


class ThirdServiceConf(Base):
    __tablename__ = 'third_service_conf'

    third_service_conf_id = Column(
        BigInteger, primary_key=True, autoincrement=True)
    service_conf_id = Column(
        BigInteger, ForeignKey('service_conf.service_conf_id', ondelete='CASCADE'), unique=True, nullable=True)
    service_name = Column(String(64), nullable=False)
    base_url = Column(Text, nullable=False)
    http_method = Column(String(8), nullable=False, default='GET')
    headers_json = Column(JSON, nullable=False, default={})
    config_json = Column(JSON, nullable=False, default={})
    mapping_json = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now())


class UrlReported(Base):
    __tablename__ = 'url_reported'

    url_reported_id = Column(BigInteger, primary_key=True, autoincrement=True)
    url_report_id = Column(
        BigInteger, ForeignKey('url_report.url_report_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='SET NULL'), nullable=False)
    action = Column(String(32), nullable=False)
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)
    remark = Column(String(256), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())


class SystemConfig(Base):
    __tablename__ = 'system_config'

    system_config_id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_key = Column(String(64), nullable=False, unique=True)
    config_value = Column(Text, nullable=False)
    description = Column(String(256), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False,
                        server_default=func.now(), onupdate=func.now())
