import pytest
from pydantic import ValidationError

from app.core.config import Settings


VALID_SETTINGS = {
    "DATABASE_URL": "postgresql+psycopg://dashboard:test-password@localhost:5432/endpoint_dashboard",
    "APP_ENV": "development",
    "APP_SECRET_KEY": "test_secret_key_minimum_32_characters",
    "ENCRYPTION_KEY": "6dJOCl4_S_8sETZSReLhjQRS8vnhRJ-UJXgt867Ia_k=",
    "ADMIN_API_KEY": "admin-test-key",
    "OPERATOR_API_KEY": "operator-test-key",
    "READONLY_API_KEY": "read-test-key",
    "SCHEDULER_LOCK_KEY": 81317077,
}


def build_settings(**overrides) -> Settings:
    payload = dict(VALID_SETTINGS)
    payload.update(overrides)
    return Settings(_env_file=None, **payload)


def test_rejects_insecure_default_database_url() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL cannot use the insecure default value"):
        build_settings(DATABASE_URL="postgresql+psycopg://dashboard:changeme@postgres:5432/endpoint_dashboard")


def test_rejects_non_psycopg_database_url() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL must start with postgresql\\+psycopg://"):
        build_settings(DATABASE_URL="postgresql://dashboard:test@localhost:5432/endpoint_dashboard")


def test_requires_valid_fernet_key() -> None:
    with pytest.raises(ValidationError, match="ENCRYPTION_KEY must be a valid Fernet key"):
        build_settings(ENCRYPTION_KEY="invalid-fernet-key")


def test_scheduler_lock_key_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="SCHEDULER_LOCK_KEY must be a positive integer"):
        build_settings(SCHEDULER_LOCK_KEY=0)


def test_requires_api_keys_in_production() -> None:
    with pytest.raises(
        ValidationError,
        match="ADMIN_API_KEY, OPERATOR_API_KEY and READONLY_API_KEY are required in production",
    ):
        build_settings(APP_ENV="production", ADMIN_API_KEY="", OPERATOR_API_KEY="", READONLY_API_KEY="")


def test_allows_missing_api_keys_in_development() -> None:
    settings = build_settings(APP_ENV="development", ADMIN_API_KEY="", OPERATOR_API_KEY="", READONLY_API_KEY="")
    assert settings.APP_ENV == "development"
