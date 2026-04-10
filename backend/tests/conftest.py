import os


# Ensure app settings can initialize during tests and module imports.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://dashboard:test-password@localhost:5432/endpoint_dashboard",
)
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("APP_SECRET_KEY", "test_secret_key_minimum_32_characters")
os.environ.setdefault("ENCRYPTION_KEY", "6dJOCl4_S_8sETZSReLhjQRS8vnhRJ-UJXgt867Ia_k=")
os.environ.setdefault("ADMIN_API_KEY", "admin-test-key")
os.environ.setdefault("OPERATOR_API_KEY", "operator-test-key")
os.environ.setdefault("READONLY_API_KEY", "read-test-key")
os.environ.setdefault("SCHEDULER_LOCK_KEY", "81317077")
