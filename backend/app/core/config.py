from functools import lru_cache
from typing import List
import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application configuration loaded from environment variables."""

    secret_key: str = Field(default=os.getenv("SECRET_KEY", "iot-management-secret-key-2024"))
    jwt_algorithm: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"))
    app_name: str = Field(default="IoT Management System")
    environment: str = Field(default=os.getenv("ENVIRONMENT", "development"))
    database_url: str = Field(
        default=os.getenv(
            "DATABASE_URL",
            "sqlite:///" + os.path.join(os.getcwd(), "data", "iot.db"),
        )
    )
    access_token_expire_minutes: int = Field(
        default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    )
    reservation_timeout_minutes: int = Field(
        default=int(os.getenv("RESERVATION_TIMEOUT_MINUTES", "30"))
    )
    reservation_check_interval_seconds: int = Field(
        default=int(os.getenv("RESERVATION_CHECK_INTERVAL_SECONDS", "60"))
    )
    cors_origins: List[str] = Field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS", "http://localhost:8080,http://frontend"
        ).split(",")
    )
    audit_log_retention_days: int = Field(
        default=int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "180"))
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
