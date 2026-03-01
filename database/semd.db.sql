BEGIN;

SET TIME ZONE 'UTC+7';
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- ENUMS
-- ============================================================

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
    CREATE TYPE user_role AS ENUM ('guest','member','admin','super_admin');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'access_permission') THEN
    CREATE TYPE access_permission AS ENUM ('global','private');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'url_type') THEN
    CREATE TYPE url_type AS ENUM ('malicious','benign');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'url_report_status') THEN
    CREATE TYPE url_report_status AS ENUM ('pending','accepted','rejected');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'usage_type') THEN
    CREATE TYPE usage_type AS ENUM ('predict','access_key');
  END IF;
END$$;

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE users (
  user_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username       TEXT UNIQUE NOT NULL,
  email          TEXT UNIQUE NOT NULL,
  full_name      TEXT,
  password_hash  TEXT,
  role           user_role DEFAULT 'member',

  google_id       TEXT,
  google_acctoken TEXT,
  google_retoken  TEXT,

  gh_id           TEXT,
  gh_acctoken     TEXT,
  gh_retoken      TEXT,

  is_twofa_enable BOOLEAN DEFAULT FALSE,
  twofa_secret    TEXT,
  twofa_recodes   TEXT,

  ex_access_token CHAR(6),
  ex_expire_time  TIMESTAMPTZ,

  birthday        TIMESTAMPTZ,
  profile_img_uri TEXT,

  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- SERVICE CONF
-- ============================================================

CREATE TABLE service_conf (
  service_conf_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id          BIGINT REFERENCES users(user_id) ON DELETE CASCADE,

  service_name     TEXT NOT NULL,
  service_type     TEXT NOT NULL,
  access           access_permission DEFAULT 'private',

  config_uri       TEXT,
  config_json      JSONB DEFAULT '{}'::jsonb,

  created_at       TIMESTAMPTZ DEFAULT now(),
  updated_at       TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- MODEL REGISTRY
-- ============================================================

CREATE TABLE model_registry (
  model_registry_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  service_conf_id   BIGINT UNIQUE REFERENCES service_conf(service_conf_id) ON DELETE CASCADE,

  name              TEXT NOT NULL,
  algorithm         TEXT NOT NULL,
  mlflow_id         TEXT,

  model_uri         TEXT,
  scaler_uri        TEXT,
  label_uri         TEXT,

  accuracy_score    NUMERIC(6,5),
  recall_score      NUMERIC(6,5),
  precision_score   NUMERIC(6,5),
  f1_score          NUMERIC(6,5),

  config_json       JSONB DEFAULT '{}'::jsonb,

  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ACCESS KEY
-- ============================================================

CREATE TABLE access_key (
  access_key_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id          BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
  access_key_hash  TEXT UNIQUE NOT NULL,
  expired_at       TIMESTAMPTZ,
  created_at       TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- PREDICTION
-- ============================================================

CREATE TABLE prediction (
  prediction_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id          BIGINT REFERENCES users(user_id) ON DELETE CASCADE,

  url              TEXT NOT NULL,
  accuracy_score   NUMERIC(6,5),
  recall_score     NUMERIC(6,5),
  precision_score  NUMERIC(6,5),
  f1_score         NUMERIC(6,5),

  suggested_desc   TEXT,
  created_at       TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- USAGE LOG
-- ============================================================

CREATE TABLE usage_log (
  usage_log_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  type             usage_type NOT NULL,
  service_id       BIGINT REFERENCES service_conf(service_conf_id),
  access_key_id    BIGINT REFERENCES access_key(access_key_id),
  prediction_id    BIGINT REFERENCES prediction(prediction_id),
  created_at       TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- URL FLAG
-- ============================================================

CREATE TABLE url_flag (
  url_flag_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  url            TEXT NOT NULL,
  type           url_type DEFAULT 'benign',
  access         access_permission DEFAULT 'private',

  user_id        BIGINT REFERENCES users(user_id),
  created_by_id  BIGINT REFERENCES users(user_id),
  updated_by_id  BIGINT REFERENCES users(user_id),

  created_at     TIMESTAMPTZ DEFAULT now(),
  updated_at     TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- URL REPORT
-- ============================================================

CREATE TABLE url_report (
  url_report_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id        BIGINT REFERENCES users(user_id),
  url            TEXT NOT NULL,
  categories     url_type DEFAULT 'benign',
  status         url_report_status DEFAULT 'pending',
  remark         TEXT,
  created_at     TIMESTAMPTZ DEFAULT now(),
  updated_at     TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- ACTIVITY LOG
-- ============================================================

CREATE TABLE activity_log (
  activity_log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id         BIGINT REFERENCES users(user_id),
  method          TEXT,
  endpoint        TEXT,
  request_id      TEXT UNIQUE,
  client_ip       INET,
  client_agent    TEXT,
  response        JSONB DEFAULT '{}'::jsonb,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

COMMIT;
