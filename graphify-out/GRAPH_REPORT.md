# Graph Report - .  (2026-07-18)

## Corpus Check
- 212 files · ~114,351 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1264 nodes · 3996 edges · 66 communities (45 shown, 21 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 547 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Model Registry Control
- Prediction and URL Flags
- Access Key Administration
- Service Configuration Control
- Prediction Validation Flow
- API Key Schemas
- URL Report Control
- API Key Analytics
- Dashboard API Stubs
- Authentication Control
- User Request Models
- Response and Token Models
- System Configuration Control
- OAuth Authentication Models
- Queue Management
- ML Job Models
- Base Routing
- Prediction Service Logic
- Redis Client Operations
- Application Factory
- Third Party Errors
- Authentication Routes
- Application Settings
- Authentication Service
- Auth Guard and Usage
- ML Service Client
- Error Handler Middleware
- PostgreSQL Client
- ML Training Routes
- Graphify Tooling
- Health Readiness Checks
- Application Entry Point
- Application Boot Tests
- ML Training Tests
- Two Factor Authentication
- Access Key Tests
- Application Exceptions
- Authentication Guard
- Authentication Error Tests
- Error Handler Tests
- Queue Permission Tests
- Model Registry Tests
- Redis Result Worker
- User Service
- HTTP Middleware Types
- Authorization Design Gaps
- Database Documentation
- Database Schema Alignment
- Audit Transaction Gaps
- Credential Storage
- URL Security Handling
- Worker Package
- Entity Relationship Diagram
- Migration Recommendations
- Unused Audit Table
- Redis Polling
- Unimplemented Dashboard Endpoints
- Retraining Pipeline Gap
- Extension Secret Safety
- URL Report State
- Problem Details Responses
- Structured Logging
- ORM Typing Gap
- Repository Root

## God Nodes (most connected - your core abstractions)
1. `User` - 211 edges
2. `BaseResponseModel` - 105 edges
3. `AuthGuard` - 72 edges
4. `RoleType` - 72 edges
5. `AuthControl` - 59 edges
6. `NotImplementedFeatureError` - 52 edges
7. `AuthRoute` - 48 edges
8. `BaseRoute` - 44 edges
9. `MLRoute` - 34 edges
10. `AuthService` - 33 edges

## Surprising Connections (you probably didn't know these)
- `RedisLiveConnectionTests` --uses--> `Settings`  [INFERRED]
  tests/unit/test_settings_redis.py → config/settings.py
- `AuthControl` --uses--> `RoleType`  [INFERRED]
  control/auth_control.py → libs/types/enums.py
- `AuthControl` --uses--> `AuthLoginProviderRequest`  [INFERRED]
  control/auth_control.py → models/auth/auth_model.py
- `AuthControl` --uses--> `AuthLoginRequest`  [INFERRED]
  control/auth_control.py → models/auth/auth_model.py
- `AuthControl` --uses--> `CreateUserRequest`  [INFERRED]
  control/auth_control.py → models/auth/auth_model.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Prediction Processing and Accountability Flow** — docs_backend_features_url_evaluation_readme_url_ssrf_protection, docs_backend_features_background_workers_redis_readme_async_redis_polling, docs_backend_features_system_audit_logs_readme_audit_logging_gap [INFERRED 0.85]
- **Privileged Mutation Authorization Pattern** — docs_backend_features_users_roles_permissions_readme_object_level_authorization, docs_backend_features_url_flags_whitelist_readme_global_flag_authorization, docs_backend_features_ml_model_registry_prediction_readme_model_registry_admin_authorization [INFERRED 0.85]

## Communities (66 total, 21 thin omitted)

### Community 0 - "Model Registry Control"
Cohesion: 0.05
Nodes (47): ModelRegistryControl, Any, AsyncSession, Decimal, Model Registry Control - Business logic layer for model registry operations., List all models (admin only)., ModelStageType, ModelRegistry (+39 more)

### Community 1 - "Prediction and URL Flags"
Cohesion: 0.07
Nodes (45): Session, UrlFlagControl, PermissionDeniedError, ACLType, FlagType, Enum, str, ReportStatusType (+37 more)

### Community 2 - "Access Key Administration"
Cohesion: 0.09
Nodes (25): AccessKeyControl, Any, Session, create_pagination_meta(), paginate_list(), PaginatedResponse, PaginationMeta, PaginationParams (+17 more)

### Community 3 - "Service Configuration Control"
Cohesion: 0.06
Nodes (27): AsyncSession, ServiceConfControl, AsyncSession, ThirdServiceControl, get_async_db(), ServiceConf, ThirdServiceConf, BaseModel (+19 more)

### Community 4 - "Prediction Validation Flow"
Cohesion: 0.06
Nodes (30): PredictionControl, Any, ValidationError, check_url_safety(), check_url_safety_async(), _is_blocked_ip(), URL-safety validation (SSRF defense-in-depth).  Wired into `control/prediction_c, Resolve `hostname` and check every returned address against the same     blockli (+22 more)

### Community 5 - "API Key Schemas"
Cohesion: 0.08
Nodes (44): ApiEndpointStatItem, ApiKeyStatItem, ApiKeyTrendItem, ApiKeyUsageItem, BaseModel, PredictionByModelItem, PredictionByModelResponse, PredictionDetailItem (+36 more)

### Community 6 - "URL Report Control"
Cohesion: 0.12
Nodes (20): Base, Session, UrlReportControl, ActivityLog, RefreshToken, UrlReport, UrlReported, ReportListResponse (+12 more)

### Community 7 - "API Key Analytics"
Cohesion: 0.06
Nodes (14): ApiKeyStatService, Any, PredictionStatService, Any, Any, ReportStatService, Any, SystemStatService (+6 more)

### Community 8 - "Dashboard API Stubs"
Cohesion: 0.11
Nodes (14): _register_routers(), NotImplementedFeatureError, A registered, authenticated endpoint whose business logic hasn't been     built, User, DashboardRoute, All 8 endpoints below were previously unauthenticated `pass` stubs     that retu, ApiKeyStatRoute, See routers/dashboard/dashboard_route.py's docstring -- same finding     (unauth (+6 more)

### Community 9 - "Authentication Control"
Cohesion: 0.12
Nodes (7): AuthControl, Session, PreAuthResponse, TokenPairResponse, OAuthService, any, Session

### Community 10 - "User Request Models"
Cohesion: 0.13
Nodes (15): BaseModel, Public-facing user profile shape.      Deliberately excludes password_hash, gg_a, UserModel, AdminCreateUserRequest, AdminPasswordResetRequest, AdminUpdateUserRequest, PasswordResetRequest, BaseModel (+7 more)

### Community 11 - "Response and Token Models"
Cohesion: 0.12
Nodes (25): BaseModel, RefreshTokenModel, BaseResponseModel, ErrorResponse422, BaseModel, MLServiceResponse, ApiEndpointStatResponse, ApiKeyStatResponse (+17 more)

### Community 12 - "System Configuration Control"
Cohesion: 0.20
Nodes (12): Session, SystemConfigControl, SystemConfig, BaseModel, SystemConfigModel, SystemConfigUpdateRequest, Session, SystemConfigListResponse (+4 more)

### Community 13 - "OAuth Authentication Models"
Cohesion: 0.35
Nodes (21): OAuthProviderType, RoleType, AuthLoginProviderRequest, AuthLoginRequest, AuthLoginResponse, AuthTwoFactorRequest, CreateUserRequest, CreateUserResponse (+13 more)

### Community 14 - "Queue Management"
Cohesion: 0.15
Nodes (13): Any, QueueControl, get_db(), ActivityLogModel, BaseModel, PredictByInfo, BaseModel, QueueItem (+5 more)

### Community 15 - "ML Job Models"
Cohesion: 0.14
Nodes (17): JobStatus, JobType, PredictionDetail, PredictionJobRequest, PredictionJobResult, BaseModel, Enum, str (+9 more)

### Community 16 - "Base Routing"
Cohesion: 0.13
Nodes (6): BaseRoute, SettingRoute, See routers/dashboard/dashboard_route.py's docstring -- same finding     (unauth, ThirdPartyStatRoute, See routers/dashboard/dashboard_route.py's docstring -- same finding     (unauth, UserStatRoute

### Community 17 - "Prediction Service Logic"
Cohesion: 0.16
Nodes (10): AsyncSession, is_class_malicious(), map_prediction_class(), normalize_class_name(), PredictionService, Any, AsyncSession, PredictionStorageService (+2 more)

### Community 18 - "Redis Client Operations"
Cohesion: 0.11
Nodes (11): Any, Push data to a Redis queue (list)., Pop data from a Redis queue (blocking)., Get cached data by key., Set cached data with TTL (default 1 hour)., Delete cached data by key., RedisClient, _fresh_client_with_settings() (+3 more)

### Community 19 - "Application Factory"
Cohesion: 0.18
Nodes (15): _configure_middleware(), create_application(), FastAPI, FastAPI application factory.  Extracted from main.py so app construction has no, _register_root_endpoints(), BaseHTTPMiddleware, configure_logging(), JsonFormatter (+7 more)

### Community 20 - "Third Party Errors"
Cohesion: 0.23
Nodes (9): ExternalServiceError, Upstream dependency (ML service, third-party detector, OAuth provider) failed., A required dependency (DB, Redis, ML queue) is unreachable or timed out., ServiceUnavailableError, Any, ThirdServiceExecutor, _fake_conf(), Domain 6: ThirdServiceExecutor error handling.  Before this change, connection e (+1 more)

### Community 21 - "Authentication Routes"
Cohesion: 0.18
Nodes (3): UserUpdateRequest, AuthRoute, Session

### Community 22 - "Application Settings"
Cohesion: 0.16
Nodes (8): BaseSettings, get_settings(), Application configuration settings using Pydantic., Configuration values, resolved as env var -> backend.ini -> built-in default., Build PostgreSQL connection URL., Return cached settings instance., Settings, RedisSettingsPrecedenceTests

### Community 24 - "Auth Guard and Usage"
Cohesion: 0.23
Nodes (10): AuthGuard, Verify both API key and Bearer token.          Args:             x_api_key: API, Prediction, Config, AsyncSession, BaseModel, RecentActivityResponse, UsageLogResponse (+2 more)

### Community 25 - "ML Service Client"
Cohesion: 0.20
Nodes (5): MLServiceClient, Any, Poll the Redis result cache for `job_id`.          Uses `asyncio.sleep`, not `ti, GetJobResultConcurrencyTests, Domain 12: get_job_result previously used blocking `time.sleep` in its poll loop

### Community 26 - "Error Handler Middleware"
Cohesion: 0.32
Nodes (14): _error_response(), handle_app_error(), handle_http_exception(), handle_unexpected_error(), handle_validation_error(), Exception, FastAPI, Request (+6 more)

### Community 27 - "PostgreSQL Client"
Cohesion: 0.13
Nodes (7): PostgresClient, AsyncSession, Session, Get database session with context manager., Get a new session instance., Get async database session with context manager., Get a new async session instance.

### Community 28 - "ML Training Routes"
Cohesion: 0.26
Nodes (8): APIRouter, NotFoundError, JobResultRequest, MLTrainingRouter, BaseModel, Was completely unregistered dead code until this pass (Domain 10) --     not exp, TrainingJobRequest, TrainingJobResponse

### Community 29 - "Graphify Tooling"
Cohesion: 0.41
Nodes (11): build_graph(), build_graph_lines(), build_wiki_lines(), cmd_graph(), cmd_wiki(), help_text(), install_hook(), main() (+3 more)

### Community 30 - "Health Readiness Checks"
Cohesion: 0.24
Nodes (6): _check_database(), _check_redis(), Liveness/readiness endpoints.  `GET /health` (main app root) returns static plac, readiness(), PostgreSQL client using SQLAlchemy., Redis client for caching and queue operations.

### Community 31 - "Application Entry Point"
Cohesion: 0.20
Nodes (6): main(), Entrypoint: builds the FastAPI app via the application factory and exposes the d, CLI entry point for running the FastAPI application., DashboardStubEndpointTests, _fake_user(), Domain 9: the 32 Dashboard/Stat endpoints were unauthenticated `pass` stubs that

### Community 33 - "ML Training Tests"
Cohesion: 0.24
Nodes (4): _admin(), _member(), MLTrainingRouteTests, Domain 10: MLTrainingRouter was completely unregistered (not exported, not inclu

### Community 35 - "Access Key Tests"
Cohesion: 0.29
Nodes (4): AccessKeyErrorHandlingTests, _fake_user(), Domain 3 (API Access Keys) error-handling sweep.  Unlike auth, most of this file, Domain 4 fix: previously stored the raw token in User.ex_acc_token.         The

### Community 36 - "Application Exceptions"
Cohesion: 0.31
Nodes (7): AppError, ConflictError, Exception, RateLimitError, Typed application-exception hierarchy.  `control/`/`services/` code should raise, Base class for typed, expected application errors.      status: the HTTP status, UnauthorizedError

### Community 37 - "Authentication Guard"
Cohesion: 0.22
Nodes (4): _get_current_user(), Session, Authentication guard for API key and Bearer token verification., Guard module for authentication.

### Community 38 - "Authentication Error Tests"
Cohesion: 0.22
Nodes (3): AuthErrorHandlingTests, Characterizes the auth-domain error-handling fix (Phase 3 sample).  Before this, Regression test for the mangled-to-500 bug: this used to come back         as 50

### Community 39 - "Error Handler Tests"
Cohesion: 0.28
Nodes (3): _build_test_app(), ErrorHandlerTests, FastAPI

### Community 40 - "Queue Permission Tests"
Cohesion: 0.28
Nodes (4): _admin(), _member(), QueueRoutePermissionTests, Domain 11: GET /queue/url exposes other users' username/user_id/ profile_img_url

### Community 41 - "Model Registry Tests"
Cohesion: 0.32
Nodes (3): _member(), MlModelRegistryPermissionTests, Domain 10: the most severe finding of this audit. Every ML model-registry mutati

### Community 42 - "Redis Result Worker"
Cohesion: 0.36
Nodes (3): main(), MLResultWorker, Redis worker for processing ML prediction results. This worker listens to ml_res

### Community 44 - "HTTP Middleware Types"
Cohesion: 0.50
Nodes (3): Request, RequestResponseEndpoint, Response

### Community 45 - "Authorization Design Gaps"
Cohesion: 0.50
Nodes (4): URL Flag URL Index Candidate, Model Registry Admin Authorization, Global URL Flag Authorization, Object Level Authorization

### Community 47 - "Database Schema Alignment"
Cohesion: 0.67
Nodes (3): Database Documentation, ORM Foreign Key Alignment, URL Reported User Constraint Contradiction

## Knowledge Gaps
- **15 isolated node(s):** `semd-backend`, `ORM Foreign Key Alignment`, `Entity Relationship Diagram`, `Unused Activity Log Table`, `Hashed API Key Storage` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Dashboard API Stubs` to `Model Registry Control`, `Prediction and URL Flags`, `Access Key Administration`, `Service Configuration Control`, `URL Report Control`, `Authentication Control`, `User Request Models`, `Response and Token Models`, `System Configuration Control`, `OAuth Authentication Models`, `Queue Management`, `ML Job Models`, `Base Routing`, `Prediction Service Logic`, `Authentication Routes`, `Application Settings`, `Authentication Service`, `Auth Guard and Usage`, `ML Training Routes`, `Application Entry Point`, `ML Training Tests`, `Two Factor Authentication`, `Access Key Tests`, `Authentication Guard`, `Queue Permission Tests`, `Model Registry Tests`?**
  _High betweenness centrality (0.272) - this node is a cross-community bridge._
- **Why does `BaseResponseModel` connect `Response and Token Models` to `Prediction and URL Flags`, `Access Key Administration`, `Service Configuration Control`, `API Key Schemas`, `URL Report Control`, `Authentication Control`, `User Request Models`, `System Configuration Control`, `OAuth Authentication Models`, `Queue Management`, `ML Job Models`, `Application Factory`, `Authentication Routes`, `ML Training Routes`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `RoleType` connect `OAuth Authentication Models` to `Prediction and URL Flags`, `Access Key Administration`, `ML Training Tests`, `Authentication Guard`, `URL Report Control`, `Queue Permission Tests`, `Authentication Control`, `User Request Models`, `Model Registry Tests`, `System Configuration Control`, `Prediction Service Logic`, `Authentication Routes`, `Authentication Service`, `Auth Guard and Usage`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `User` (e.g. with `.login_2fa()` and `_get_current_user()`) actually correct?**
  _`User` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `BaseResponseModel` (e.g. with `AuthLoginProviderRequest` and `AuthLoginRequest`) actually correct?**
  _`BaseResponseModel` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 43 inferred relationships involving `AuthGuard` (e.g. with `RoleType` and `AuthService`) actually correct?**
  _`AuthGuard` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 50 inferred relationships involving `RoleType` (e.g. with `AuthControl` and `AuthGuard`) actually correct?**
  _`RoleType` has 50 INFERRED edges - model-reasoned connections that need verification._