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
    def fake_start_sync_run(data_source_id: int | None = None, force: bool = False):
        return (
            {
                "run_id": "fake-run-id",
                "data_source_id": data_source_id,
                "force": force,
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


def test_sync_run_force_query_bypasses_interval_guardrail(client: TestClient, monkeypatch) -> None:
    captured_force: dict[str, bool] = {"value": False}

    def fake_start_sync_run(data_source_id: int | None = None, force: bool = False):
        captured_force["value"] = force
        return (
            {
                "run_id": "force-run-id",
                "data_source_id": data_source_id,
                "force": force,
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

    response = client.post("/api/sync/run?force=true", headers=_headers("operator-test-key"))
    assert response.status_code == 200
    assert response.json()["accepted"] is True
    assert response.json()["run_id"] == "force-run-id"
    assert captured_force["value"] is True


def test_settings_source_can_be_deleted(client: TestClient) -> None:
    create_settings = client.post(
        "/api/settings/blob",
        headers=_headers("admin-test-key"),
        json={
            "name": "delete-me-source",
            "account_url": "https://example.blob.core.windows.net",
            "container_name": "inventory",
            "sas_token": "sv=fake-token-for-tests",
            "blob_prefix": "",
            "sync_frequency_minutes": 480,
            "is_active": True,
        },
    )
    assert create_settings.status_code == 200
    source_id = create_settings.json()["id"]

    delete_response = client.delete(f"/api/settings/blob/{source_id}", headers=_headers("admin-test-key"))
    assert delete_response.status_code == 204

    list_response = client.get("/api/settings/blob", headers=_headers("admin-test-key"))
    assert list_response.status_code == 200
    assert all(s["id"] != source_id for s in list_response.json())


def test_metrics_requires_auth_and_exposes_request_id(client: TestClient) -> None:
    no_auth_metrics = client.get("/metrics")
    assert no_auth_metrics.status_code == 401

    health = client.get("/health")
    assert health.status_code == 200
    assert health.headers.get("X-Request-ID")

    auth_metrics = client.get("/metrics", headers=_headers("read-test-key"))
    assert auth_metrics.status_code == 200
    assert "endpoint_dashboard_http_requests_total" in auth_metrics.text
