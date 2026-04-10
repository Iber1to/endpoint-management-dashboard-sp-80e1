from __future__ import annotations

from cryptography.fernet import Fernet
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://dashboard:changeme@postgres:5432/endpoint_dashboard"
    APP_ENV: str = "production"
    APP_SECRET_KEY: str = "change_this_secret_key_min_32_chars_long!!"
    ENCRYPTION_KEY: str = ""
    DEFAULT_TIMEZONE: str = "Europe/Madrid"

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://frontend"]

    ADMIN_API_KEY: str = ""
    OPERATOR_API_KEY: str = ""
    READONLY_API_KEY: str = ""

    PATCH_CATALOG_SYNC_INTERVAL_MINUTES: int = 1440
    INVENTORY_SYNC_INTERVAL_MINUTES: int = 60
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_LOCK_KEY: int = 81317077

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("DATABASE_URL is required")
        if normalized == "postgresql+psycopg://dashboard:changeme@postgres:5432/endpoint_dashboard":
            raise ValueError("DATABASE_URL cannot use the insecure default value")
        if not normalized.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must start with postgresql+psycopg://")
        return normalized

    @field_validator("APP_SECRET_KEY")
    @classmethod
    def validate_app_secret_key(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 32:
            raise ValueError("APP_SECRET_KEY must be at least 32 characters")
        if normalized == "change_this_secret_key_min_32_chars_long!!":
            raise ValueError("APP_SECRET_KEY cannot use the insecure default value")
        return normalized

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("ENCRYPTION_KEY is required")
        try:
            Fernet(normalized.encode("utf-8"))
        except Exception as exc:
            raise ValueError("ENCRYPTION_KEY must be a valid Fernet key") from exc
        return normalized

    @field_validator("SCHEDULER_LOCK_KEY")
    @classmethod
    def validate_scheduler_lock_key(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("SCHEDULER_LOCK_KEY must be a positive integer")
        return value

    @model_validator(mode="after")
    def validate_production_auth_keys(self) -> "Settings":
        if self.APP_ENV.lower() != "production":
            return self

        if not (self.ADMIN_API_KEY and self.OPERATOR_API_KEY and self.READONLY_API_KEY):
            raise ValueError(
                "ADMIN_API_KEY, OPERATOR_API_KEY and READONLY_API_KEY are required in production"
            )
        return self


settings = Settings()
