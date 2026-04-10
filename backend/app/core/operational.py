from __future__ import annotations

from app.core.config import settings

_INSECURE_API_KEYS = {
    "admin-test-key",
    "operator-test-key",
    "read-test-key",
    "admin-local-key",
    "operator-local-key",
    "read-local-key",
}


def security_warnings() -> list[str]:
    warnings: list[str] = []

    if settings.APP_ENV.lower() != "production":
        return warnings

    if settings.APP_SECRET_KEY == "change_this_secret_key_min_32_chars_long!!":
        warnings.append("APP_SECRET_KEY is using a known insecure default value")

    key_map = {
        "ADMIN_API_KEY": settings.ADMIN_API_KEY,
        "OPERATOR_API_KEY": settings.OPERATOR_API_KEY,
        "READONLY_API_KEY": settings.READONLY_API_KEY,
    }
    for key_name, key_value in key_map.items():
        if key_value in _INSECURE_API_KEYS:
            warnings.append(f"{key_name} is using a non-production test value")
        if key_value and len(key_value) < 16:
            warnings.append(f"{key_name} is shorter than 16 characters")

    return warnings
