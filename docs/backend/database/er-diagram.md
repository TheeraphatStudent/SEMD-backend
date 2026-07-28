# ER Diagram (as-implemented)

Reflects `database/models.py` post-Phase-3 `ForeignKey()` additions, cross-checked against `database/semd.db.sql`'s actual DDL constraints.

```mermaid
erDiagram
    USERS ||--o{ REFRESH_TOKENS : "owns (CASCADE)"
    USERS ||--o{ SERVICE_CONF : "configures (CASCADE)"
    USERS ||--o{ ACCESS_KEY : "owns (CASCADE)"
    USERS ||--o{ PREDICTION : "requests (SET NULL)"
    USERS ||--o{ URL_FLAG : "defines (CASCADE)"
    USERS ||--o{ URL_REPORT : "submits (CASCADE)"
    USERS ||--o{ ACTIVITY_LOG : "generates (SET NULL) -- table unused, see system-audit-logs finding"
    USERS ||--o{ URL_REPORTED : "acts_on (SET NULL, contradicts NOT NULL -- see table-dictionary.md)"
    SERVICE_CONF ||--o| MODEL_REGISTRY : "registers (CASCADE)"
    SERVICE_CONF ||--o| THIRD_SERVICE_CONF : "configures (CASCADE)"
    ACCESS_KEY ||--o{ USAGE_LOG : "tracked_by (SET NULL)"
    SERVICE_CONF ||--o{ USAGE_LOG : "tracked_by (SET NULL)"
    PREDICTION ||--o{ USAGE_LOG : "tracked_by (SET NULL)"
    URL_REPORT ||--o{ URL_REPORTED : "has_history (CASCADE)"
    SYSTEM_CONFIG {
        bigint system_config_id PK
        string config_key UK
    }
```

`SYSTEM_CONFIG` has no foreign keys in or out — shown standalone for completeness (config_key/value pairs, admin-managed via `/setting/system-config`).

Not shown as a relationship (no FK exists): `USAGE_LOG` and `PREDICTION`/`URL_REPORT`/`URL_FLAG` are all conceptually linked to "which URL was evaluated," but there is no `url` foreign-key table — `url` is a plain `Text` column repeated across `prediction.url`, `url_flag.url`, `url_report.url`, with no shared `url_record` entity the way the master prompt's example ER diagram assumed (`URL_REPORT }o--|| URL_RECORD`). Confirmed: no such table exists in this schema.
