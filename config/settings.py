"""Application configuration settings using Pydantic."""

from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings
import configparser

config = configparser.ConfigParser()
config.read("./backend.ini")
config.sections()

class Settings(BaseSettings):
    """Configuration values loaded from environment variables."""

    # App settings
    app_name: str = config.get("API", "APP_NAME", fallback="SEMD API")
    app_version: str = config.get("API", "VERSION", fallback="1.0.0")
    debug: bool = config.getboolean("API", "DEBUG", fallback=False)

    # PostgreSQL settings
    postgres_host: str = config.get("POSTGRESQL", "HOST", fallback="localhost")
    postgres_port: int = config.getint("POSTGRESQL", "PORT", fallback=5432)
    postgres_user: str = config.get("POSTGRESQL", "USER", fallback="postgres")
    postgres_password: str = config.get("POSTGRESQL", "PASSWORD", fallback="")
    postgres_db: str = config.get("POSTGRESQL", "DB", fallback="semd_db")

    # Redis settings
    redis_host: str = config.get("REDIS", "HOST", fallback="localhost")
    redis_port: int = config.getint("REDIS", "PORT", fallback=6379)
    redis_password: str = config.get("REDIS", "PASSWORD", fallback="")
    redis_db: int = config.getint("REDIS", "DB", fallback=0)

    # MLflow settings
    mlflow_tracking_uri: str = config.get("MLFLOW", "TRACKING_URL", fallback="http://localhost:5000")

    # API Key
    api_key: str = config.get("API", "KEY_TEST", fallback="test-api-key")

    # JWT settings
    jwt_secret: str = config.get("JWT", "SECRET", fallback="your-secret-key")
    jwt_algorithm: str = config.get("JWT", "ALGORITHM", fallback="HS256")

    # Auth settings
    auth_secret_key: str = config.get("AUTH", "SECRET_KEY", fallback="your-secret-key-here")
    auth_algorithm: str = config.get("AUTH", "ALGORITHM", fallback="HS256")
    auth_access_token_expire_minutes: int = config.getint("AUTH", "ACCESS_TOKEN_EXPIRE_MINUTES", fallback=15)
    auth_refresh_token_expire_days: int = config.getint("AUTH", "REFRESH_TOKEN_EXPIRE_DAYS", fallback=7)

    # GitHub OAuth settings
    github_client_id: str = config.get("GITHUB", "CLIENT_ID", fallback="")
    github_client_secret: str = config.get("GITHUB", "CLIENT_SECRET", fallback="")
    github_redirect_uri: str = config.get("GITHUB", "REDIRECT_URI", fallback="http://localhost:8000/auth/callback/github")
    github_homepage_url: str = config.get("GITHUB", "HOMEPAGE_URL", fallback="http://localhost:8000")

    # Google OAuth settings
    google_client_id: str = config.get("GOOGLE", "CLIENT_ID", fallback="")
    google_client_secret: str = config.get("GOOGLE", "CLIENT_SECRET", fallback="")
    google_redirect_uri: str = config.get("GOOGLE", "REDIRECT_URI", fallback="http://localhost:8000/auth/callback/google")

    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
