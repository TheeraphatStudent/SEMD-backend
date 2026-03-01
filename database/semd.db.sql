-- ============================================================
-- 1. สร้าง ENUM TYPES (อ้างอิงจาก Column Type ใน Design)
-- ============================================================

DO $$ 
BEGIN
    -- สำหรับตาราง users
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'role_type') THEN
        CREATE TYPE role_type AS ENUM ('GUEST', 'MEMBER', 'ADMIN', 'SUPER_ADMIN');
    END IF;

    -- สำหรับตาราง url_flag
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'flag_type') THEN
        CREATE TYPE flag_type AS ENUM ('MALICIOUS', 'BENIGN');
    END IF;

    -- สำหรับตาราง url_flag (Access Level)
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'acl_type') THEN
        CREATE TYPE acl_type AS ENUM ('GLOBAL', 'PRIVATE');
    END IF;

    -- สำหรับตาราง url_report (Status)
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'rp_status_type') THEN
        CREATE TYPE rp_status_type AS ENUM ('PENDING', 'ACCEPTED', 'REJECTED');
    END IF;

    -- สำหรับตาราง usage_log
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'usage_log_type') THEN
        CREATE TYPE usage_log_type AS ENUM ('PREDICT', 'ACCESS_KEY');
    END IF;

    -- สำหรับตาราง service_conf
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'service_type') THEN
        CREATE TYPE service_type AS ENUM ('REST_API', 'WEB_HOOK', 'SDK');
    END IF;
END $$;

-- ============================================================
-- 2. สร้าง TABLES
-- ============================================================

-- ตารางผู้ใช้งาน (Users)
CREATE TABLE IF NOT EXISTS users (
    user_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username        VARCHAR(32) UNIQUE NOT NULL,
    email           VARCHAR(64) UNIQUE NOT NULL,
    full_name       VARCHAR(512) NOT NULL,
    password_hash   VARCHAR(1024) NOT NULL,
    role            role_type NOT NULL DEFAULT 'MEMBER',
    
    -- Social Auth & 2FA
    gg_id           TEXT NULL,
    gg_acc_token    TEXT NULL,
    gg_re_token     TEXT NULL,
    gh_id           TEXT NULL,
    gh_acc_token    TEXT NULL,
    gh_re_token     TEXT NULL,
    twofa_secret    TEXT NULL,
    
    -- Extension & Profile
    ex_acc_token     TEXT NULL,
    ex_acc_token_exp TIMESTAMPTZ NULL,
    profile_img_uri  TEXT NULL,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ตารางจัดการบริการ (Service Config)
CREATE TABLE IF NOT EXISTS service_conf (
    service_conf_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    service_name    VARCHAR(32) NOT NULL,
    service_type    service_type NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    version_no      VARCHAR(12) NOT NULL,
    config_uri      TEXT NOT NULL,
    config_json     JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ตารางโมเดลที่ลงทะเบียน (Model Registry) - MLflow 3.x
CREATE TABLE IF NOT EXISTS model_registry (
    model_registry_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_conf_id      BIGINT UNIQUE REFERENCES service_conf(service_conf_id) ON DELETE CASCADE,
    name                 VARCHAR(64) NOT NULL,
    algorithm            VARCHAR(64) NOT NULL,
    
    -- MLflow 3.x specific fields
    mlflow_run_id        VARCHAR(64) NOT NULL,
    mlflow_model_version INT NULL,
    experiment_id        VARCHAR(64) NULL,
    stage                model_stage_type NOT NULL DEFAULT 'NONE',
    
    -- Artifact URIs
    model_uri            TEXT NOT NULL,
    scaler_uri           TEXT NOT NULL,
    label_uri            TEXT NOT NULL,
    selecter_uri         TEXT NOT NULL,
    
    -- Metrics (0.0000 to 1.0000)
    accuracy_score       NUMERIC(5, 4) NULL,
    recall_score         NUMERIC(5, 4) NULL,
    precision_score      NUMERIC(5, 4) NULL,
    f1_score             NUMERIC(5, 4) NULL,
    
    -- Metadata
    description          TEXT NULL,
    tags                 JSONB NOT NULL DEFAULT '{}',
    
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ตารางรหัสเข้าถึง (Access Key)
CREATE TABLE IF NOT EXISTS access_key (
    access_key_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    access_key_hash TEXT NOT NULL,
    expired_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ตารางผลการทำนาย (Prediction)
CREATE TABLE IF NOT EXISTS prediction (
    prediction_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    url             TEXT NOT NULL,

    -- Metrics
    accuracy_score  NUMERIC(10, 2) NULL,
    recall_score    NUMERIC(10, 2) NULL,
    precision_score NUMERIC(10, 2) NULL,
    f1_score        NUMERIC(10, 2) NULL,

    -- Suggested Description
    suggested_desc  VARCHAR(512) NULL,
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ตารางรายการ URL Flag
CREATE TABLE IF NOT EXISTS url_flag (
    url_flag_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    type            flag_type NOT NULL DEFAULT 'BENIGN',
    access_level    acl_type NOT NULL DEFAULT 'PRIVATE',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ตารางรายงาน URL (URL Report)
CREATE TABLE IF NOT EXISTS url_report (
    url_report_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    url             TEXT NOT NULL,
    categories      flag_type NOT NULL DEFAULT 'BENIGN',
    status          rp_status_type NOT NULL DEFAULT 'PENDING',
    remark          VARCHAR(256) NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ตารางบันทึกเหตุการณ์ (Activity Log)
CREATE TABLE IF NOT EXISTS activity_log (
    activity_log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id         BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    method          VARCHAR(16) NOT NULL,
    endpoint        VARCHAR(1024) NOT NULL,
    request_id      VARCHAR(32) UNIQUE NOT NULL,
    client_ip       VARCHAR(32) NULL,
    client_agent    VARCHAR(256) NULL,
    response        VARCHAR(512) NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ตารางบันทึกการใช้งาน (Usage Log)
CREATE TABLE IF NOT EXISTS usage_log (
    usage_log_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id      BIGINT REFERENCES service_conf(service_conf_id) ON DELETE SET NULL,
    access_key_id   BIGINT REFERENCES access_key(access_key_id) ON DELETE SET NULL,
    prediction_id   BIGINT REFERENCES prediction(prediction_id) ON DELETE SET NULL,
    type            usage_log_type NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ตารางบริการภายนอก (Third Service Conf)
CREATE TABLE IF NOT EXISTS third_service_conf (
    third_service_conf_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_name          VARCHAR(64) NOT NULL,
    base_url              TEXT NOT NULL,
    http_method           VARCHAR(8) NOT NULL DEFAULT 'GET',
    secret_hash           TEXT NOT NULL,                  -- Format: key1:value1;key2:value2;
    headers_json          JSONB NOT NULL DEFAULT '{}',
    config_json           JSONB NOT NULL DEFAULT '{}',
    is_active             BOOLEAN NOT NULL DEFAULT TRUE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);