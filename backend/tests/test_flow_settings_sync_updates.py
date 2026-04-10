from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.routes.sync as sync_routes
import app.db.models  # noqa: F401
import app.main as main_module
from app.db.base import Base
from app.db.session import get_db


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(main_module, "start_scheduler", lambda: None)
    monkeypatch.setattr(main_module, "stop_scheduler", lambda: None)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[get_db] = override_get_db
    with TestClient(main_module.app) as test_client:
        yield test_client

    main_module.app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _headers(api_key: str) -> dict[str, str]:
    return {"X-API-Key": api_key}


def test_settings_sync_updates_end_to_end(client: TestClient, monkeypatch) -> None:
    def fake_start_sync_run(data_source_id: int | None = None):
        return (
            {
                "run_id": "fake-run-id",
                "data_source_id": data_source_id,
                "status": "queued",
                "requested_at": datetime.now(timezone.utc),
                "started_at": None,
                "finished_at": None,
                "duration_seconds": None,
                "stats": {
                    "total": 0,
                    "processed": 0,
                    "errors": 0,
                    "skipped": 0,
                    "by_type": {
                        "hardware": {"discovered": 0, "processed": 0, "errors": 0, "skipped": 0},
                        "software": {"discovered": 0, "processed": 0, "errors": 0, "skipped": 0},
                    },
                },
                "sources_total": 1,
                "sources_failed": [],
                "evaluation_failed": False,
                "message": None,
            },
            None,
            None,
        )

    monkeypatch.setattr(sync_routes, "start_sync_run", fake_start_sync_run)

    create_settings = client.post(
        "/api/settings/blob",
        headers=_headers("admin-test-key"),
        json={
            "name": "integration-source",
            "account_url": "https://example.blob.core.windows.net",
            "container_name": "inventory",
            "sas_token": "sv=fake-token-for-tests",
            "blob_prefix": "endpoints/",
            "sync_frequency_minutes": 480,
            "is_active": True,
        },
    )
    assert create_settings.status_code == 200
    assert create_settings.json()["name"] == "integration-source"

    sync_response = client.post("/api/sync/run", headers=_headers("operator-test-key"))
    assert sync_response.status_code == 200
    assert sync_response.json()["accepted"] is True
    assert sync_response.json()["run_id"] == "fake-run-id"


def test_metrics_requires_auth_and_exposes_request_id(client: TestClient) -> None:
    no_auth_metrics = client.get("/metrics")
    assert no_auth_metrics.status_code == 401

    health = client.get("/health")
    assert health.status_code == 200
    assert health.headers.get("X-Request-ID")

    auth_metrics = client.get("/metrics", headers=_headers("read-test-key"))
    assert auth_metrics.status_code == 200
    assert "endpoint_dashboard_http_requests_total" in auth_metrics.text
