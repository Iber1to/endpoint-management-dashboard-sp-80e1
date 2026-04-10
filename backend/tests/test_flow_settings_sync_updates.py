from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.routes.sync as sync_routes
import app.db.models  # noqa: F401
import app.main as main_module
from app.db.base import Base
from app.db.models import Endpoint, EndpointSnapshot, InventoryFile, WindowsPatchReference, WindowsUpdateStatus
from app.db.models.datasource import DataSource
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
    def fake_run_sync(db: Session, source: DataSource) -> dict:
        inventory_file = InventoryFile(
            data_source_id=source.id,
            blob_name="hardware-PC01-20260410-120000.json",
            file_type="hardware",
            endpoint_name="PC01",
            status="processed",
            processed_at=datetime.now(timezone.utc),
        )
        db.add(inventory_file)
        source.last_sync_status = "success"
        source.last_sync_at = datetime.now(timezone.utc)
        db.commit()
        return {"total": 1, "processed": 1, "errors": 0, "skipped": 0}

    def fake_evaluate_all_updates(db: Session) -> dict:
        endpoint = Endpoint(endpoint_key="PC01", computer_name="PC01")
        db.add(endpoint)
        db.flush()

        snapshot = EndpointSnapshot(
            endpoint_id=endpoint.id,
            snapshot_at=datetime.now(timezone.utc),
            is_current=True,
        )
        db.add(snapshot)
        db.flush()

        patch_ref = WindowsPatchReference(
            product_name="Windows 11",
            windows_version="24H2",
            full_build="26100.3775",
            kb_article="KB5053598",
            patch_month="2026-04",
            patch_label="2026-04 Update",
            release_date=date(2026, 4, 10),
            is_preview=False,
            is_latest_for_branch=True,
            scraped_at=datetime.now(timezone.utc),
            catalog_version="20260410",
        )
        db.add(patch_ref)

        update_status = WindowsUpdateStatus(
            endpoint_id=endpoint.id,
            snapshot_id=snapshot.id,
            windows_version="24H2",
            full_build="26100.3775",
            kb_article="KB5053598",
            patch_month="2026-04",
            patch_label="2026-04 Update",
            compliance_status="up_to_date",
            months_behind=0,
            inferred=False,
            evaluated_at=datetime.now(timezone.utc),
        )
        db.add(update_status)
        db.commit()
        return {"evaluated": 1, "errors": 0}

    monkeypatch.setattr(sync_routes, "run_sync", fake_run_sync)
    monkeypatch.setattr(sync_routes, "evaluate_all_updates", fake_evaluate_all_updates)

    create_settings = client.post(
        "/api/settings/blob",
        headers=_headers("admin-test-key"),
        json={
            "name": "integration-source",
            "account_url": "https://example.blob.core.windows.net",
            "container_name": "inventory",
            "sas_token": "sv=fake-token-for-tests",
            "blob_prefix": "endpoints/",
            "sync_frequency_minutes": 60,
            "is_active": True,
        },
    )
    assert create_settings.status_code == 200
    assert create_settings.json()["name"] == "integration-source"

    sync_response = client.post("/api/sync/run", headers=_headers("operator-test-key"))
    assert sync_response.status_code == 200
    assert sync_response.json()["success"] is True
    assert sync_response.json()["stats"]["processed"] == 1

    compliance_response = client.get("/api/updates/compliance", headers=_headers("read-test-key"))
    assert compliance_response.status_code == 200
    payload = compliance_response.json()
    assert payload["target_patch"] == "2026-04"
    assert payload["summary"]["total"] == 1
    assert payload["summary"]["up_to_date"] == 1
    assert payload["items"][0]["computer_name"] == "PC01"
    assert payload["items"][0]["compliance_status"] == "up_to_date"


def test_metrics_requires_auth_and_exposes_request_id(client: TestClient) -> None:
    no_auth_metrics = client.get("/metrics")
    assert no_auth_metrics.status_code == 401

    health = client.get("/health")
    assert health.status_code == 200
    assert health.headers.get("X-Request-ID")

    auth_metrics = client.get("/metrics", headers=_headers("read-test-key"))
    assert auth_metrics.status_code == 200
    assert "endpoint_dashboard_http_requests_total" in auth_metrics.text
