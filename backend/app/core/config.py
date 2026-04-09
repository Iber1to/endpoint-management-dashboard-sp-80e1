from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg://dashboard:changeme@postgres:5432/endpoint_dashboard"
    APP_ENV: str = "production"
    APP_SECRET_KEY: str = "change_this_secret_key_min_32_chars_long!!"
    ENCRYPTION_KEY: str = ""
    DEFAULT_TIMEZONE: str = "Europe/Madrid"

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://frontend"]

    PATCH_CATALOG_SYNC_INTERVAL_MINUTES: int = 1440
    INVENTORY_SYNC_INTERVAL_MINUTES: int = 60


settings = Settings()
